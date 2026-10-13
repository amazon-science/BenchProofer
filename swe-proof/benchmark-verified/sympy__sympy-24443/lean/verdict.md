# P2 adversarial audit — sympy__sympy-24443

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TIGHT IFF over a fully DEEP model with EMPTY A-legs (no axioms, no opaque callees): problem_spec_checkRelators genOf imageOf rels result := (result = true) <-> forall r in rels, evalWord genOf imageOf r = 1, where evalWord is defined structurally as the ordered product of imageOf(genOf s)^p over the word. Any impl that closes correct_checkRelators must therefore be extensionally equal to decide(spec); there is no loophole for a wrong impl. All 7 same-spec wrong impls fail to verify with the natural gold proof. Machine-checked disproof of the atk_3 theorem verifies (disproof_3.lean EXIT=0), confirming the spec genuinely rejects wrong impls (theorem is FALSE, not merely hard to prove).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,6 +37,7 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
@@ -46,13 +47,13 @@
       let mut acc : G := 1
       for sp in r do
         let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
+        if sp.2 ≥ 0 then
+          acc := acc * imageOf g ^ sp.2
       return acc
     if w ≠ 1 then
       return false
   return true
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,6 +37,7 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
@@ -46,13 +47,12 @@
       let mut acc : G := 1
       for sp in r do
         let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
+        acc := acc * imageOf g ^ (sp.2.natAbs : Int)
       return acc
     if w ≠ 1 then
       return false
   return true
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,22 +37,12 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
-    (rels : List (List (Sym × Int))) : Bool := Id.run do
-  for r in rels do
-    let w : G := Id.run do
-      let mut acc : G := 1
-      for sp in r do
-        let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
-      return acc
-    if w ≠ 1 then
-      return false
-  return true
+    (rels : List (List (Sym × Int))) : Bool := true
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,22 +37,12 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
-    (rels : List (List (Sym × Int))) : Bool := Id.run do
-  for r in rels do
-    let w : G := Id.run do
-      let mut acc : G := 1
-      for sp in r do
-        let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
-      return acc
-    if w ≠ 1 then
-      return false
-  return true
+    (rels : List (List (Sym × Int))) : Bool := rels.isEmpty
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,6 +37,7 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
@@ -46,13 +47,12 @@
       let mut acc : G := 1
       for sp in r do
         let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
+        acc := imageOf g ^ sp.2 * acc
       return acc
     if w ≠ 1 then
       return false
   return true
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,22 +37,21 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
-    (rels : List (List (Sym × Int))) : Bool := Id.run do
-  for r in rels do
+    (rels : List (List (Sym × Int))) : Bool :=
+  match rels with
+  | [] => true
+  | r :: _ =>
     let w : G := Id.run do
       let mut acc : G := 1
       for sp in r do
-        let g := genOf sp.1
-        acc := acc * imageOf g ^ sp.2
+        acc := acc * imageOf (genOf sp.1) ^ sp.2
       return acc
-    if w ≠ 1 then
-      return false
-  return true
+    w = 1
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,6 +37,7 @@
   (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
     (genOf : Sym → Gen) (imageOf : Gen → G)
@@ -44,7 +45,7 @@
   for r in rels do
     let w : G := Id.run do
       let mut acc : G := 1
-      for sp in r do
+      for sp in r.dropLast do
         let g := genOf sp.1
         acc := acc * imageOf g ^ sp.2
       return acc
@@ -52,7 +53,6 @@
       return false
   return true
 -- impl-end
-
 
 -- proof-start
 theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The codomain is a genuine
-- group, so its multiplication, integer powers, and identity are modeled with
-- Mathlib's `Group` structure (not axiomatized). The two finite lookups
-- (symbol → generator, generator → codomain element) are modeled as ordinary
-- total functions supplied as inputs. The word-evaluation is modeled DEEPLY
-- (`evalWord`, a product over the word); it consumes no opaque callee, so there
-- is no A-consumed axiom and no A-reference `opaque` declaration. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The codomain element a relator word evaluates to under a valuation of
generators. A word is a list of `(symbol, exponent)` pairs; each symbol names a
generator (`genOf`) whose assigned codomain element is `imageOf`, and the word's
value is the ordered product of those elements raised to their exponents.
Front-recursive so the accumulator loop in the implementation can be related to
it by induction. -/
def evalWord {Sym Gen G : Type*} [Group G]
    (genOf : Sym → Gen) (imageOf : Gen → G) : List (Sym × Int) → G
  | [] => 1
  | (s, p) :: rest => imageOf (genOf s) ^ p * evalWord genOf imageOf rest
-- pure-end

-- post-conditions-start
/-- A valuation of generators (`genOf` mapping each symbol to a generator,
`imageOf` mapping each generator to an element of the codomain group) extends to
a homomorphism of the presented group exactly when every defining relator word
evaluates to the codomain identity. The decision result is `true` precisely in
that case. -/
def problem_spec_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) (result : Bool) : Prop :=
  (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
-- post-conditions-end

-- impl-start
def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) : Bool := Id.run do
  for r in rels do
    let w : G := Id.run do
      let mut acc : G := 1
      for sp in r do
        let g := genOf sp.1
        acc := acc * imageOf g ^ sp.2
      return acc
    if w ≠ 1 then
      return false
  return true
-- impl-end


-- proof-start
theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) :
    problem_spec_checkRelators genOf imageOf rels
      (implementation_checkRelators genOf imageOf rels) := by
  have inner_loop : ∀ (r : List (Sym × Int)) (acc : G),
      (forIn r acc (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = acc * evalWord genOf imageOf r := by
    intro r
    induction r with
    | nil => intro acc; simp [evalWord]; rfl
    | cons hd tl ih =>
      intro acc
      rw [List.forIn_cons]
      show forIn tl (acc * imageOf (genOf hd.1) ^ hd.2) _ = _
      rw [ih]
      obtain ⟨s, p⟩ := hd
      simp [evalWord, mul_assoc]
  simp only [problem_spec_checkRelators, implementation_checkRelators, Id.run, bind, pure]
  have key : ∀ r : List (Sym × Int),
      (forIn r 1 (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = evalWord genOf imageOf r := by
    intro r; rw [inner_loop]; simp
  simp only [key]
  induction rels with
  | nil => simp
  | cons hd tl ih =>
    rw [List.forIn_cons]
    by_cases hw : evalWord genOf imageOf hd = 1
    · simp only [hw, ne_eq, not_true_eq_false, if_false]
      simp only [List.forall_mem_cons, hw, true_and]; exact ih
    · simp [hw]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Bundle spec byte-identical prefix (lines 1-39) copied verbatim; only impl+proof regions edited. same_spec elides impl AND proof regions -> all 8 files (7 attacks + pos_control) return same_spec=True (verified with swebench_unified.markers.same_spec via lean backend).

POSITIVE CONTROL: pos_control.lean -> `bash scripts/lean_verify.sh pos_control.lean` EXIT=0. `#print axioms correct_checkRelators` -> [propext, Quot.sound] (clean, no sorryAx/native).

### ATTACKS (each = same-spec wrong impl + VERBATIM gold proof body; run via lean_verify.sh, concurrent background jobs <=4):
 - atk_1 partial-domain/control-flow (PREPATCH BUG: `if sp.2>=0 then acc:=...` skips negative-exponent/inverted-generator entries): EXIT=1 (does NOT verify).
 - atk_2 boundary (natAbs exponent -> drops sign, inverse becomes forward power): EXIT=1.
 - atk_3 ungrounded-oracle (impl := true): EXIT=1.
 - atk_4 ungrounded-oracle (impl := rels.isEmpty): EXIT=1.
 - atk_5 boundary (reversed product order acc := imageOf g ^ p * acc): EXIT=1.
 - atk_6 control-flow-effect (checks only the FIRST relator, ignores rest): EXIT=1.
 - atk_7 boundary/off-by-one (r.dropLast -> drops last factor of each word): EXIT=1.
All 7 fail; NONE closes with clean axioms, therefore NO verifying-but-wrong impl exists and no faithful refined patch needs to be materialized/resolved (patches={}).

DISPROOF: disproof_3.lean gives a monomorphic counterexample (G=Multiplicative (ZMod 2), one generator mapped to ofAdd 1, one relator [(sym,1)]): proves `not (problem_spec_checkRelators ... (implementation:=true))`. EXIT=0 -> machine-checked evidence the atk_3 correctness theorem is genuinely FALSE, so lean_verify EXIT=1 reflects an unprovable (false) goal, not insufficient proof effort.

REFINEMENT AUDIT: refinement.md legs 1-7 all tagged R or I; no kind-3 (changed-inexpressible). A-legs legitimately EMPTY: word value built directly from total-function inputs (genOf, imageOf) using Mathlib Group primitives (*, ^:Int, 1); modeled DEEPLY via evalWord; no consumed callee axiom, no A-reference opaque decl. axiom_check.py is a genuine skip stub (status=skip) consistent with empty axioms region. mapping.md type bijection sound: Int exponent carries the inverted-generator sign the bug mishandled (g^(-1)=g^{-1} in Mathlib). A-leg/model-correspondence therefore holds; the R/I legs are G-CONF's domain.

CONCLUSION: verify => correct holds for this bundle within the audited attack surface. Tight-iff + deep-model + empty-A leaves no gap; >=7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle) all rejected; positive control verifies clean. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TIGHT IFF over a fully DEEP model with EMPTY A-legs (no axioms, no opaque callees): problem_spec_checkRelators genOf imageOf rels result := (result = true) <-> forall r in rels, evalWord genOf imageOf r = 1, where evalWord is defined structurally as the ordered product of imageOf(genOf s)^p over the word. Any impl that closes correct_checkRelators must therefore be extensionally equal to decide(spec); there is no loophole for a wrong impl. All 7 same-spec wrong impls fail to verify with the natural gold proof. Machine-checked disproof of the atk_3 theorem verifies (disproof_3.lean EXIT=0), confirming the spec genuinely rejects wrong impls (theorem is FALSE, not merely hard to prove).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature. The codomain is a genuine
-- group, so its multiplication, integer powers, and identity are modeled with
-- Mathlib's `Group` structure (not axiomatized). The two finite lookups
-- (symbol → generator, generator → codomain element) are modeled as ordinary
-- total functions supplied as inputs. The word-evaluation is modeled DEEPLY
-- (`evalWord`, a product over the word); it consumes no opaque callee, so there
-- is no A-consumed axiom and no A-reference `opaque` declaration. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The codomain element a relator word evaluates to under a valuation of
generators. A word is a list of `(symbol, exponent)` pairs; each symbol names a
generator (`genOf`) whose assigned codomain element is `imageOf`, and the word's
value is the ordered product of those elements raised to their exponents.
Front-recursive so the accumulator loop in the implementation can be related to
it by induction. -/
def evalWord {Sym Gen G : Type*} [Group G]
    (genOf : Sym → Gen) (imageOf : Gen → G) : List (Sym × Int) → G
  | [] => 1
  | (s, p) :: rest => imageOf (genOf s) ^ p * evalWord genOf imageOf rest
-- pure-end

-- post-conditions-start
/-- A valuation of generators (`genOf` mapping each symbol to a generator,
`imageOf` mapping each generator to an element of the codomain group) extends to
a homomorphism of the presented group exactly when every defining relator word
evaluates to the codomain identity. The decision result is `true` precisely in
that case. -/
def problem_spec_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) (result : Bool) : Prop :=
  (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
-- post-conditions-end

-- impl-start
def implementation_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) : Bool := Id.run do
  for r in rels do
    let w : G := Id.run do
      let mut acc : G := 1
      for sp in r do
        let g := genOf sp.1
        acc := acc * imageOf g ^ sp.2
      return acc
    if w ≠ 1 then
      return false
  return true
-- impl-end


-- proof-start
theorem correct_checkRelators {Sym Gen G : Type*} [Group G] [DecidableEq G]
    (genOf : Sym → Gen) (imageOf : Gen → G)
    (rels : List (List (Sym × Int))) :
    problem_spec_checkRelators genOf imageOf rels
      (implementation_checkRelators genOf imageOf rels) := by
  have inner_loop : ∀ (r : List (Sym × Int)) (acc : G),
      (forIn r acc (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = acc * evalWord genOf imageOf r := by
    intro r
    induction r with
    | nil => intro acc; simp [evalWord]; rfl
    | cons hd tl ih =>
      intro acc
      rw [List.forIn_cons]
      show forIn tl (acc * imageOf (genOf hd.1) ^ hd.2) _ = _
      rw [ih]
      obtain ⟨s, p⟩ := hd
      simp [evalWord, mul_assoc]
  simp only [problem_spec_checkRelators, implementation_checkRelators, Id.run, bind, pure]
  have key : ∀ r : List (Sym × Int),
      (forIn r 1 (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)
        = evalWord genOf imageOf r := by
    intro r; rw [inner_loop]; simp
  simp only [key]
  induction rels with
  | nil => simp
  | cons hd tl ih =>
    rw [List.forIn_cons]
    by_cases hw : evalWord genOf imageOf hd = 1
    · simp only [hw, ne_eq, not_true_eq_false, if_false]
      simp only [List.forall_mem_cons, hw, true_and]; exact ih
    · simp [hw]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Bundle spec byte-identical prefix (lines 1-39) copied verbatim; only impl+proof regions edited. same_spec elides impl AND proof regions -> all 8 files (7 attacks + pos_control) return same_spec=True (verified with swebench_unified.markers.same_spec via lean backend).

POSITIVE CONTROL: pos_control.lean -> `bash scripts/lean_verify.sh pos_control.lean` EXIT=0. `#print axioms correct_checkRelators` -> [propext, Quot.sound] (clean, no sorryAx/native).

### ATTACKS (each = same-spec wrong impl + VERBATIM gold proof body; run via lean_verify.sh, concurrent background jobs <=4):
 - atk_1 partial-domain/control-flow (PREPATCH BUG: `if sp.2>=0 then acc:=...` skips negative-exponent/inverted-generator entries): EXIT=1 (does NOT verify).
 - atk_2 boundary (natAbs exponent -> drops sign, inverse becomes forward power): EXIT=1.
 - atk_3 ungrounded-oracle (impl := true): EXIT=1.
 - atk_4 ungrounded-oracle (impl := rels.isEmpty): EXIT=1.
 - atk_5 boundary (reversed product order acc := imageOf g ^ p * acc): EXIT=1.
 - atk_6 control-flow-effect (checks only the FIRST relator, ignores rest): EXIT=1.
 - atk_7 boundary/off-by-one (r.dropLast -> drops last factor of each word): EXIT=1.
All 7 fail; NONE closes with clean axioms, therefore NO verifying-but-wrong impl exists and no faithful refined patch needs to be materialized/resolved (patches={}).

DISPROOF: disproof_3.lean gives a monomorphic counterexample (G=Multiplicative (ZMod 2), one generator mapped to ofAdd 1, one relator [(sym,1)]): proves `not (problem_spec_checkRelators ... (implementation:=true))`. EXIT=0 -> machine-checked evidence the atk_3 correctness theorem is genuinely FALSE, so lean_verify EXIT=1 reflects an unprovable (false) goal, not insufficient proof effort.

REFINEMENT AUDIT: refinement.md legs 1-7 all tagged R or I; no kind-3 (changed-inexpressible). A-legs legitimately EMPTY: word value built directly from total-function inputs (genOf, imageOf) using Mathlib Group primitives (*, ^:Int, 1); modeled DEEPLY via evalWord; no consumed callee axiom, no A-reference opaque decl. axiom_check.py is a genuine skip stub (status=skip) consistent with empty axioms region. mapping.md type bijection sound: Int exponent carries the inverted-generator sign the bug mishandled (g^(-1)=g^{-1} in Mathlib). A-leg/model-correspondence therefore holds; the R/I legs are G-CONF's domain.

CONCLUSION: verify => correct holds for this bundle within the audited attack surface. Tight-iff + deep-model + empty-A leaves no gap; >=7 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle) all rejected; positive control verifies clean. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find a divergence; spec is FAITHFUL to real post-patch _check_homomorphism (PermutationGroup leg).

(1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean backend) = True. problem_spec_checkRelators/evalWord unchanged.

(2) Proof genuine: lean_verify.sh exit 0; #print axioms correct_checkRelators = [propext, Quot.sound], no sorryAx.

(3) Spec = (result=true ↔ ∀ r∈rels, evalWord genOf imageOf r = 1), modeling post-patch _image fold w *= images[symbols_to_domain_generators[symbol]]**power with early reject on non-identity. Front-recursive product equals iterative accumulator by group associativity; Int exponent gives genuine inverse (g^(-1)=g⁻¹) = **power for negative power (the repaired inverted-generator case).

(4) Empirical fidelity vs REAL gold-patched sympy@809c53c: conformance_check.py ran 120025 cases (incl. bug-report homomorphism(D3,D3,D3.generators,D3.generators) and identity/trivial boundaries) with 0 disagreements against real _check_homomorphism. Independent exhaustive sweep of all generator→element assignments over D3/C4/S3/D4 (140 cases): 0 disagreements.

(5) FpGroup-codomain leg (real routes through codomain.equals/rewriting) is deliberately out of modeled scope per mapping.md — a scoping choice, not spec-too-strong drift; within the declared PermutationGroup scope the modeled function agrees with the real callee on every tested input. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean, lean flavor) exposes only: imports, an axioms doc comment, the `evalWord` pure helper (ordered product of generator images raised to integer exponents), and the `problem_spec_checkRelators` post-condition (result=true iff every relator word evaluates to the codomain identity). impl and proof regions are elided to placeholders.

Mechanical leakage.screen PASSES (hard_failures=[]): no diff markers, no patched file path (homomorphisms.py absent), no narration terms (bug/fix/broken/etc. absent), no distinctive patched-symbol echo. The only patch-changed distinctive symbol is `homomorphism`; the sole spec-view occurrence of 'homomorphism' is in prose ('a homomorphism of the presented group ...') — and this term is public: the problem_statement is titled `_check_homomorphism is broken on PermutationGroups` and shows `homomorphism(D3, D3, ...)`. So it does not leak beyond problem_statement.

The gold edit's specifics are entirely absent from the spec view: no `_image`, no `symbols_to_domain_generators` precomputed table, no `array_form`, no `in gens` membership recovery, no domain.generators/ext_rep. The post-condition is the implementation-agnostic mathematical spec of the routine; the `^ p` integer-power model (handling inverted generators uniformly) mirrors correct group theory, and the public problem_statement itself already names inverted generators as the failure mode ('When r[i] is an inverted generator, the in gens test fails').

Decisive check: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) == True — the prepatch (buggy) and postpatch (gold) bundles have a byte-identical spec view. The gold/buggy discriminator lives wholly in the elided impl region, so the spec view provably cannot reconstruct the gold edit beyond the public problem statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
