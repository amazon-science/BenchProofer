# P2 adversarial audit — sympy__sympy-12419

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified, so the protocol's "materialize the faithful patch and run run_resolve" trigger never fired -- patches={} for that reason, not for cost/time. The absence is STRUCTURAL, and I proved it mechanically rather than inferring it from exhausted ideas: freedom.lean (verified, exit 0) contains `theorem spec_is_functional : out1 = entryFor i j eq kd -> out2 = entryFor i j eq kd -> out1 = out2`, plus one uniqueness `example` per realizable verdict class. Clause `ensures out = entryFor i j eq kd` therefore determines the output UNIQUELY from (i,j,eq,kd); there is no precondition, no `mut` param, no module-level axiom (`grep -nE '^\s*axiom' Solution.lean` => NONE), and entryFor/coincideValue are transparent constructor expressions with no opaque answer node. Any verifying impl is thus extensionally the gold value on every input, leaving zero residual freedom for a value-level wrong-but-verifying impl. That is why each attack died on a NAMED discriminating ensures rather than on tactic weakness.

TWO OVER-PINNING observations (resolve-but-not-verify; direction is spec STRICTER than the oracle, so neither refutes verify=>correct, but both are G-PANEL-2 material): (1) real KroneckerDelta.eval canonicalizes operand order (tensor_functions.py `if i is not min(i,j,key=default_sort_key): return cls(j,i)`), measured: KD(i,j)==KD(j,i) is True and real _entry(j,i)==KroneckerDelta(i,j). So the Lean carrier (coincide i j != coincide j i) is FINER than the library quotient. I executed the consequence: patch_flip.diff (`return KroneckerDelta(j, i)`), which the spec REJECTS via atk_4/ensures_2, RESOLVED=True completed=True. (2) atk_12 (`coincide i i`) is rejected by ensures_2 as it should be.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,19 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+      return MatEntry.null
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,25 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
       let e : MatEntry :=
         if eq = some false then MatEntry.null
         else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
+          if kd = some true then MatEntry.null
+          else if kd = some false then MatEntry.unit
           else MatEntry.coincide i j
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,22 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
       let e : MatEntry :=
         if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
+        else MatEntry.coincide i j
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,6 +151,7 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
@@ -159,10 +160,16 @@
         else
           if kd = some true then MatEntry.unit
           else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
+          else MatEntry.coincide j i
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,28 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
-    if eq = some true then
-      return MatEntry.unit
+
+    if i.id = 0 then
+      return MatEntry.null
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+      if eq = some true then
+        return MatEntry.unit
+      else
+        let e : MatEntry :=
+          if eq = some false then MatEntry.null
+          else
+            if kd = some true then MatEntry.unit
+            else if kd = some false then MatEntry.null
+            else MatEntry.coincide i j
+        return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,34 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
+      if eq = some false then
+        return MatEntry.null
+      else
+        if kd = some true then
+          return MatEntry.unit
         else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+          if kd = some false then
+            return MatEntry.null
+          else
+            let mut spin : Nat := 1
+            while spin > 0
+              invariant spin > 0
+              decreasing spin
+            do
+              spin := spin + 1
+            return MatEntry.coincide i j
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,16 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
-    if eq = some true then
-      return MatEntry.unit
-    else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+
+    return MatEntry.coincide i j
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,25 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
-    if eq = some true then
+
+    if kd = some true then
       return MatEntry.unit
     else
       let e : MatEntry :=
-        if eq = some false then MatEntry.null
+        if kd = some false then MatEntry.null
         else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
+          if eq = some true then MatEntry.unit
+          else if eq = some false then MatEntry.null
           else MatEntry.coincide i j
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,6 +151,7 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
@@ -159,10 +160,17 @@
         else
           if kd = some true then MatEntry.unit
           else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
+          else if i.id < i.id then MatEntry.coincide i j
+          else MatEntry.null
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,12 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
       let e : MatEntry :=
-        if eq = some false then MatEntry.null
+        if eq = some false then MatEntry.coincide i j
         else
           if kd = some true then MatEntry.unit
           else if kd = some false then MatEntry.null
@@ -165,4 +166,10 @@
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,31 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+      let mut acc : MatEntry := MatEntry.null
+      let mut k : Nat := 0
+      while k < 2
+        invariant k ≤ 2
+        decreasing 2 - k
+      do
+        acc :=
+          (if eq = some false then MatEntry.null
+           else if kd = some true then MatEntry.unit
+           else if kd = some false then MatEntry.null
+           else MatEntry.null)
+        k := k + 1
+      return acc
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,6 +151,7 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
@@ -159,10 +160,16 @@
         else
           if kd = some true then MatEntry.unit
           else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
+          else MatEntry.coincide i i
       return e
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,20 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+      let (v : MatEntry) :| v ≠ MatEntry.unit
+      return v
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,29 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
+
     if eq = some true then
       return MatEntry.unit
     else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
+      if eq = some false then
+        return MatEntry.null
+      else
+        if kd = some true then
+          return MatEntry.unit
         else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+          if kd = some false then
+            return MatEntry.null
+          else
+            let (v : MatEntry) :| (v = MatEntry.coincide i j ∨ v = MatEntry.null)
+            return v
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,18 +151,17 @@
   ensures eq = none → kd = none → out ≠ MatEntry.null
   do
     -- impl-start
-    if eq = some true then
-      return MatEntry.unit
-    else
-      let e : MatEntry :=
-        if eq = some false then MatEntry.null
-        else
-          if kd = some true then MatEntry.unit
-          else if kd = some false then MatEntry.null
-          else MatEntry.coincide i j
-      return e
+
+    let (v : MatEntry) :| v = entryFor i j eq kd
+    return v
     -- impl-end
 
 prove_correct identityEntry by
   loom_solve
-  all_goals simp_all [entryFor, coincideValue]
+  all_goals try simp_all [entryFor, coincideValue]
+  all_goals try grind
+  all_goals try (simp [entryFor, coincideValue])
+  all_goals try rfl
+  all_goals try omega
+  all_goals try trivial
+  all_goals try aesop
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour modeled is the choice of element value for a
   square diagonal-of-units operator at a symbolic position. The decision rests
   on two three-valued verdicts, each produced by a separate primitive and
   supplied to the method as an input: the verdict of comparing the two
   positions, and the coincidence indicator's OWN self-evaluation at those
   positions. Their agreement with the real primitives is exercised end-to-end by
   the conformance check (G-CONF); there is no module-level `axiom`. Provenance:
   mapping.md §3. -/
-- axioms-end

-- pure-start
/- A position into the operator: an opaque symbolic index. Two positions carry
   no decidable structure here — whether they coincide is decided by the
   three-valued verdicts that are passed in, NOT by inspecting the carrier — so
   this is just an abstract atom that the result may refer to. -/
structure Idx where
  id : Nat
deriving DecidableEq, Inhabited

/- The element value of a diagonal-of-units operator at one position. It is an
   honest symbolic-value carrier with NO opaque "answer" node:

     • `unit`        — the multiplicative unit,
     • `null`        — the additive zero,
     • `coincide a b`— the symbolic coincidence indicator of the two positions,
                       left UNEVALUATED: the value that becomes the unit or the
                       zero only once the coincidence of `a` and `b` is settled.

   The `coincide` node refers to the actual positions `a b`, so the result on the
   unsettled case is forced to be *produced by* the operands; a builder that did
   not consult them could not emit this node. -/
inductive MatEntry where
  | unit
  | null
  | coincide (a b : Idx)
deriving DecidableEq, Inhabited

/- Three-valued verdicts are modeled as `Option Bool`: `some true` = definitely
   coincident, `some false` = definitely distinct, `none` = unsettled (the
   question cannot be decided from what the primitive can see).

   TWO verdicts are consumed, because the operator's element value is selected in
   two stages and each stage has its OWN, DIFFERENT decision power:

     • `eq` — the verdict of the position-comparison primitive;
     • `kd` — the verdict of the coincidence indicator's own self-evaluation at
              the same two positions.

   These are NOT the same verdict. The indicator decides coincidence by its own
   rules, which see facts about the positions that the comparison primitive does
   not, so the indicator can settle a pair that the comparison leaves unsettled.
   `kd` is therefore an independent input, not a function of `eq`. -/

/- The value the coincidence indicator itself denotes at positions `i`, `j`,
   given its own three-valued self-evaluation `kd`:

     • definitely coincident (`some true`)  → the unit,
     • definitely distinct   (`some false`) → the zero,
     • unsettled             (`none`)       → the indicator, left unevaluated
                                              and referring to `i` and `j`.

   This is the indicator's contract: it is a value that COLLAPSES when its own
   rules settle the coincidence, and survives as a symbolic object only while
   they do not. -/
def coincideValue (i j : Idx) (kd : Option Bool) : MatEntry :=
  if kd = some true then MatEntry.unit
  else if kd = some false then MatEntry.null
  else MatEntry.coincide i j

/- The desired element value at positions `i`, `j` given the comparison verdict
   `eq` and the indicator's own verdict `kd`:

     • comparison definitely coincident (`some true`)  → the unit,
     • comparison definitely distinct   (`some false`) → the zero,
     • comparison UNSETTLED             (`none`)       → hand the pair to the
                                                        coincidence indicator and
                                                        take the value IT denotes.

   The second stage is itself a full three-way selection, not a single value:
   the indicator yields the unit or the zero where its own rules settle the pair,
   and remains the unevaluated indicator over the operands only where they do
   not. -/
def entryFor (i j : Idx) (eq : Option Bool) (kd : Option Bool) : MatEntry :=
  if eq = some true then MatEntry.unit
  else if eq = some false then MatEntry.null
  else coincideValue i j kd

@[grind] lemma entryFor_true (i j : Idx) (kd : Option Bool) :
    entryFor i j (some true) kd = MatEntry.unit := rfl
@[grind] lemma entryFor_false (i j : Idx) (kd : Option Bool) :
    entryFor i j (some false) kd = MatEntry.null := rfl
@[grind] lemma entryFor_none (i j : Idx) (kd : Option Bool) :
    entryFor i j none kd = coincideValue i j kd := rfl

@[grind] lemma coincideValue_true (i j : Idx) :
    coincideValue i j (some true) = MatEntry.unit := rfl
@[grind] lemma coincideValue_false (i j : Idx) :
    coincideValue i j (some false) = MatEntry.null := rfl
@[grind] lemma coincideValue_none (i j : Idx) :
    coincideValue i j none = MatEntry.coincide i j := rfl

/- When BOTH verdicts leave the coincidence unsettled the value is the
   unevaluated indicator over the two positions, which is a symbolic object
   distinct from the zero. Note the scope: the claim is made exactly where the
   indicator declines to collapse, NOT wherever the comparison declines to
   settle. Where the indicator's own rules DO settle the pair, its value is the
   unit or the zero, and the operator reports that. -/
@[grind] lemma entryFor_unsettled_ne_null (i j : Idx) :
    entryFor i j none none ≠ MatEntry.null := by
  simp [entryFor, coincideValue]

@[grind] lemma entryFor_unsettled_eq_coincide (i j : Idx) :
    entryFor i j none none = MatEntry.coincide i j := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the element value of a square diagonal-of-units operator at positions
   `i` and `j`, given the three-valued verdict `eq` of comparing the two
   positions and the three-valued verdict `kd` of the coincidence indicator's own
   self-evaluation at those same positions. Both verdicts are produced by
   separate primitives and both are read-only (neither is `mut`).

   Desired behaviour: a comparison that settles the pair yields the unit
   (coincident) or the zero (distinct). A comparison that leaves the pair
   UNSETTLED hands it to the coincidence indicator, and the result is the value
   the indicator denotes: the unit or the zero where the indicator's own rules
   settle it, and otherwise the indicator itself, unevaluated and referring to
   both operands. -/
method identityEntry (i : Idx) (j : Idx) (eq : Option Bool) (kd : Option Bool) return (out : MatEntry)
  ensures out = entryFor i j eq kd
  ensures eq = some true  → out = MatEntry.unit
  ensures eq = some false → out = MatEntry.null
  ensures eq = none → out = coincideValue i j kd
  ensures eq = none → kd = some true  → out = MatEntry.unit
  ensures eq = none → kd = some false → out = MatEntry.null
  ensures eq = none → kd = none → out = MatEntry.coincide i j
  ensures eq = none → kd = none → out ≠ MatEntry.null
  do
    -- impl-start
    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else
          if kd = some true then MatEntry.unit
          else if kd = some false then MatEntry.null
          else MatEntry.coincide i j
      return e
    -- impl-end

prove_correct identityEntry by
  loom_solve
  all_goals simp_all [entryFor, coincideValue]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of sympy__sympy-12419/velvet. 15 attacks, ALL same_spec=True + admissible=True + verifies=False + verify_completed=True, re-confirmed programmatically through the OFFICIAL primitive adversary.check_attack (not just lean_verify.sh exit codes): official.py, results in official_check.json.

### CONTROLS (all three needed to make the rejections meaningful):
  pos_control.lean (byte copy of frozen Solution.lean)  -> EXIT=0 verifies
  pos_strong.lean  (gold impl + STRICTLY STRONGER tactic) -> EXIT=0  => the added grind/rfl/omega/aesop fallbacks do not break the frozen proof, so attack rejections are SEMANTIC, not tactic-fragility. atk_2..atk_16 all ship this stronger tactic.
  atk_13.lean (LOOP POSITIVE CONTROL: same while/invariant/decreasing scaffolding as atk_11 but carrying the GOLD value) -> EXIT=0 verifies => the loop machinery is not what rejects atk_6/atk_11.
  prepatch.lean (byte copy of Solution_prepatch.lean) -> EXIT=1 on EXACTLY the 5 clauses refinement.md §B claims (ensures_1,2,4,5,8). PREPATCH BUG REPRODUCED.

### ATTACK LEDGER (exit 1 = rejected; goals = named unsolved obligations):
atk_1  prepatch bug re-encoded (zero on every non-some-true)     ensures_1,2,4(,5,8) atk_2  BOUNDARY: indicator-verdict polarity swapped              ensures_3,4 atk_3  MODEL-CORR: ignores indicator verdict, ALWAYS-uneval      ensures_3,4 atk_4  GROUNDING: operand order flipped (coincide j i)           ensures_2 atk_5  PARTIAL-DOMAIN: wrong only on slice i.id = 0              ensures_1,2,4,7 atk_6  CONTROL-FLOW-EFFECT: returns the GOLD value on every input but DIVERGES on exactly the doubly-unsettled case (the F2P input) -> rejected on `decreasing_1: spin`.

Total-correctness scope kills divergence, so a verifying impl cannot refine to a patch that hangs on the F2P input. atk_7  UNGROUNDED-ORACLE ECHO: always the indicator, ignores both verdicts  ensures_3,4,6,7 atk_8  MODEL-CORR: the two verdicts' ROLES swapped (outer reads kd, inner reads eq) -- agrees with gold wherever the verdicts agree, so it is refuted only on the POPULATED cross-class  ensures_6,7,8 atk_9  VACUITY CONTROL: discriminating branch dead behind infeasible guard `i.id < i.id` -> does NOT go vacuous  ensures_1,2 atk_10 BOUNDARY: definitely-distinct comparison handed to the indicator anyway  ensures_6 atk_11 CONTROL-FLOW: terminating loop-carried accumulator laundering the zero-collapse  ensures_1,2,3,4,6 + invariant_1 atk_12 GROUNDING: indicator over the WRONG operand pair (i,i)   ensures_2 atk_14/15/16 DEMONIC-CHOICE class -- REPORTED HONESTLY AS FAIL-CLOSED, NOT AS SEMANTIC REJECTIONS.

All three (incl. atk_16, which pins the choice to EXACTLY the gold value as the control) die on `failed to synthesize Findable fun v =>...` + `Failed to parse an assertion without names: WPGen sorry`. MatEntry has no Findable instance (Loom/MonadAlgebras/NonDetT/Findable.lean requires Encodable+DecidablePred or FinEnum+DecidablePred), so pickSuchThat/havoc is structurally UNAVAILABLE on this carrier. Because the gold-pinned control fails identically, these three prove only that the evasion fails closed -- they are NOT evidence the spec rejected a weaker predicate. The 12 semantic attacks (>= 5 floor) carry the verdict on their own.

A-LEG AUDIT (my assignment's focus; G-CONF covers R/I). Zero module-level axioms => the A-legs are A-reference only: A2 (eq = real three-valued Eq verdict), A5 (kd = KroneckerDelta's OWN self-evaluation), A6 (fall-through = the value KroneckerDelta(i,j) DENOTES). Re-derived INDEPENDENTLY against real sympy in my own fresh worktree repo_gold (base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b, `git apply patch.diff` => PATCH APPLIED CLEAN; py3.10 collections.abc shim inline):
  - aleg.py:  441 index pairs, transliterated entryFor/coincideValue through mapping.md §2's bijection vs oracle Identity(n).`_entry`(a,b) => 0 DISAGREEMENTS. Classes populated: (True,True)=29, (False,False)=44, (None,None)=360, (None,False)=8.
  - aleg2.py: broadened pool (below/above_fermi, positive/negative/zero/nonzero/even/odd, Rationals, sums, n-1, 3n) 1089 pairs => 0 DISAGREEMENTS. Exactly FOUR verdict classes are realizable: (True,True), (False,False), (None,None), (None,False). The impossible class (some true, kd != some true) never occurs, so the model carries no dead correspondence.
  - The (None,False) CROSS-CLASS IS REAL, not assumed empty: p=Symbol('p',below_fermi=True), q=Symbol('q',above_fermi=True) gives threeval=None, kdval=False, real `_entry`(p,q) = 0, model = 0. This is precisely why the model needs a SECOND verdict; the one-verdict simplification (atk_3) is unfaithful here and the spec rejects it (ensures_3). A5/A6 correspondence holds where it is load-bearing.

refinement.md AUDIT: legs A1-A6 tagged R / R+A-reference(input) / I(R on leaf) / A-reference+I -- no A-consumed (consistent with zero axioms) and NO kind-3; §C's no-kind-3 claim is accurate. Load-bearing prose claims spot-checked BY EXECUTION, not read: (a) §C/§5's Piecewise claim CONFIRMED -- piecewise_probe.py shows Piecewise((1,Eq(i,j)),(0,True)) has flat sum 3 but nested sum does NOT reduce (leaves `Piecewise((3, Eq(i,0)),...) +...`), F2P-PASS=False, while gold KroneckerDelta(i,j) gives !=0 True, flat 3, nested 3, F2P-PASS=True; (b) §B's five named unsolved goals match prepatch.lean's measured output exactly; (c) §A's hunk quote matches patch.diff verbatim and the two import-placement changes are correctly called out as behavioural no-ops outside the modeled site.

### RESOLVE LANE (EXECUTED via harness.run_resolve, docker oracle live; resolve_many.py):
  - patch_gold.diff  -> resolved=True, completed=True, attempts=1  (G-RESOLVE anchor reproduced; lane calibrated, so the flip result below is trustworthy)
  - patch_flip.diff (`return KroneckerDelta(j, i)`, the atk_4 shape the spec REJECTS) -> resolved=True, completed=True, attempts=1  (over-pinning note; resolve-but-not-verify, direction stricter)
No attack verified, so there was no faithful wrong-impl patch to resolve -- the BROKEN trigger never occurred.

**VERDICT:** SOUND. 12 semantic same-spec admissible attacks (>= 5 floor) plus 3 honestly-labelled fail-closed ones all REJECTED; positive control verifies under both the frozen and a strictly stronger tactic; loop-scaffolding and vacuity controls both behave correctly; prepatch reproduced on exactly the documented clauses; A-reference legs re-derived against real sympy with 0/1089 disagreements including the populated cross-class; and the no-counterexample claim is backed by a machine-checked Lean functionality theorem rather than by exhaustion. verify=>correct is not refuted for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong impl verified, so the protocol's "materialize the faithful patch and run run_resolve" trigger never fired -- patches={} for that reason, not for cost/time. The absence is STRUCTURAL, and I proved it mechanically rather than inferring it from exhausted ideas: freedom.lean (verified, exit 0) contains `theorem spec_is_functional : out1 = entryFor i j eq kd -> out2 = entryFor i j eq kd -> out1 = out2`, plus one uniqueness `example` per realizable verdict class. Clause `ensures out = entryFor i j eq kd` therefore determines the output UNIQUELY from (i,j,eq,kd); there is no precondition, no `mut` param, no module-level axiom (`grep -nE '^\s*axiom' Solution.lean` => NONE), and entryFor/coincideValue are transparent constructor expressions with no opaque answer node. Any verifying impl is thus extensionally the gold value on every input, leaving zero residual freedom for a value-level wrong-but-verifying impl. That is why each attack died on a NAMED discriminating ensures rather than on tactic weakness.

TWO OVER-PINNING observations (resolve-but-not-verify; direction is spec STRICTER than the oracle, so neither refutes verify=>correct, but both are G-PANEL-2 material): (1) real KroneckerDelta.eval canonicalizes operand order (tensor_functions.py `if i is not min(i,j,key=default_sort_key): return cls(j,i)`), measured: KD(i,j)==KD(j,i) is True and real _entry(j,i)==KroneckerDelta(i,j). So the Lean carrier (coincide i j != coincide j i) is FINER than the library quotient. I executed the consequence: patch_flip.diff (`return KroneckerDelta(j, i)`), which the spec REJECTS via atk_4/ensures_2, RESOLVED=True completed=True. (2) atk_12 (`coincide i i`) is rejected by ensures_2 as it should be.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour modeled is the choice of element value for a
   square diagonal-of-units operator at a symbolic position. The decision rests
   on two three-valued verdicts, each produced by a separate primitive and
   supplied to the method as an input: the verdict of comparing the two
   positions, and the coincidence indicator's OWN self-evaluation at those
   positions. Their agreement with the real primitives is exercised end-to-end by
   the conformance check (G-CONF); there is no module-level `axiom`. Provenance:
   mapping.md §3. -/
-- axioms-end

-- pure-start
/- A position into the operator: an opaque symbolic index. Two positions carry
   no decidable structure here — whether they coincide is decided by the
   three-valued verdicts that are passed in, NOT by inspecting the carrier — so
   this is just an abstract atom that the result may refer to. -/
structure Idx where
  id : Nat
deriving DecidableEq, Inhabited

/- The element value of a diagonal-of-units operator at one position. It is an
   honest symbolic-value carrier with NO opaque "answer" node:

     • `unit`        — the multiplicative unit,
     • `null`        — the additive zero,
     • `coincide a b`— the symbolic coincidence indicator of the two positions,
                       left UNEVALUATED: the value that becomes the unit or the
                       zero only once the coincidence of `a` and `b` is settled.

   The `coincide` node refers to the actual positions `a b`, so the result on the
   unsettled case is forced to be *produced by* the operands; a builder that did
   not consult them could not emit this node. -/
inductive MatEntry where
  | unit
  | null
  | coincide (a b : Idx)
deriving DecidableEq, Inhabited

/- Three-valued verdicts are modeled as `Option Bool`: `some true` = definitely
   coincident, `some false` = definitely distinct, `none` = unsettled (the
   question cannot be decided from what the primitive can see).

   TWO verdicts are consumed, because the operator's element value is selected in
   two stages and each stage has its OWN, DIFFERENT decision power:

     • `eq` — the verdict of the position-comparison primitive;
     • `kd` — the verdict of the coincidence indicator's own self-evaluation at
              the same two positions.

   These are NOT the same verdict. The indicator decides coincidence by its own
   rules, which see facts about the positions that the comparison primitive does
   not, so the indicator can settle a pair that the comparison leaves unsettled.
   `kd` is therefore an independent input, not a function of `eq`. -/

/- The value the coincidence indicator itself denotes at positions `i`, `j`,
   given its own three-valued self-evaluation `kd`:

     • definitely coincident (`some true`)  → the unit,
     • definitely distinct   (`some false`) → the zero,
     • unsettled             (`none`)       → the indicator, left unevaluated
                                              and referring to `i` and `j`.

   This is the indicator's contract: it is a value that COLLAPSES when its own
   rules settle the coincidence, and survives as a symbolic object only while
   they do not. -/
def coincideValue (i j : Idx) (kd : Option Bool) : MatEntry :=
  if kd = some true then MatEntry.unit
  else if kd = some false then MatEntry.null
  else MatEntry.coincide i j

/- The desired element value at positions `i`, `j` given the comparison verdict
   `eq` and the indicator's own verdict `kd`:

     • comparison definitely coincident (`some true`)  → the unit,
     • comparison definitely distinct   (`some false`) → the zero,
     • comparison UNSETTLED             (`none`)       → hand the pair to the
                                                        coincidence indicator and
                                                        take the value IT denotes.

   The second stage is itself a full three-way selection, not a single value:
   the indicator yields the unit or the zero where its own rules settle the pair,
   and remains the unevaluated indicator over the operands only where they do
   not. -/
def entryFor (i j : Idx) (eq : Option Bool) (kd : Option Bool) : MatEntry :=
  if eq = some true then MatEntry.unit
  else if eq = some false then MatEntry.null
  else coincideValue i j kd

@[grind] lemma entryFor_true (i j : Idx) (kd : Option Bool) :
    entryFor i j (some true) kd = MatEntry.unit := rfl
@[grind] lemma entryFor_false (i j : Idx) (kd : Option Bool) :
    entryFor i j (some false) kd = MatEntry.null := rfl
@[grind] lemma entryFor_none (i j : Idx) (kd : Option Bool) :
    entryFor i j none kd = coincideValue i j kd := rfl

@[grind] lemma coincideValue_true (i j : Idx) :
    coincideValue i j (some true) = MatEntry.unit := rfl
@[grind] lemma coincideValue_false (i j : Idx) :
    coincideValue i j (some false) = MatEntry.null := rfl
@[grind] lemma coincideValue_none (i j : Idx) :
    coincideValue i j none = MatEntry.coincide i j := rfl

/- When BOTH verdicts leave the coincidence unsettled the value is the
   unevaluated indicator over the two positions, which is a symbolic object
   distinct from the zero. Note the scope: the claim is made exactly where the
   indicator declines to collapse, NOT wherever the comparison declines to
   settle. Where the indicator's own rules DO settle the pair, its value is the
   unit or the zero, and the operator reports that. -/
@[grind] lemma entryFor_unsettled_ne_null (i j : Idx) :
    entryFor i j none none ≠ MatEntry.null := by
  simp [entryFor, coincideValue]

@[grind] lemma entryFor_unsettled_eq_coincide (i j : Idx) :
    entryFor i j none none = MatEntry.coincide i j := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the element value of a square diagonal-of-units operator at positions
   `i` and `j`, given the three-valued verdict `eq` of comparing the two
   positions and the three-valued verdict `kd` of the coincidence indicator's own
   self-evaluation at those same positions. Both verdicts are produced by
   separate primitives and both are read-only (neither is `mut`).

   Desired behaviour: a comparison that settles the pair yields the unit
   (coincident) or the zero (distinct). A comparison that leaves the pair
   UNSETTLED hands it to the coincidence indicator, and the result is the value
   the indicator denotes: the unit or the zero where the indicator's own rules
   settle it, and otherwise the indicator itself, unevaluated and referring to
   both operands. -/
method identityEntry (i : Idx) (j : Idx) (eq : Option Bool) (kd : Option Bool) return (out : MatEntry)
  ensures out = entryFor i j eq kd
  ensures eq = some true  → out = MatEntry.unit
  ensures eq = some false → out = MatEntry.null
  ensures eq = none → out = coincideValue i j kd
  ensures eq = none → kd = some true  → out = MatEntry.unit
  ensures eq = none → kd = some false → out = MatEntry.null
  ensures eq = none → kd = none → out = MatEntry.coincide i j
  ensures eq = none → kd = none → out ≠ MatEntry.null
  do
    -- impl-start
    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else
          if kd = some true then MatEntry.unit
          else if kd = some false then MatEntry.null
          else MatEntry.coincide i j
      return e
    -- impl-end

prove_correct identityEntry by
  loom_solve
  all_goals simp_all [entryFor, coincideValue]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of sympy__sympy-12419/velvet. 15 attacks, ALL same_spec=True + admissible=True + verifies=False + verify_completed=True, re-confirmed programmatically through the OFFICIAL primitive adversary.check_attack (not just lean_verify.sh exit codes): official.py, results in official_check.json.

### CONTROLS (all three needed to make the rejections meaningful):
  pos_control.lean (byte copy of frozen Solution.lean)  -> EXIT=0 verifies
  pos_strong.lean  (gold impl + STRICTLY STRONGER tactic) -> EXIT=0  => the added grind/rfl/omega/aesop fallbacks do not break the frozen proof, so attack rejections are SEMANTIC, not tactic-fragility. atk_2..atk_16 all ship this stronger tactic.
  atk_13.lean (LOOP POSITIVE CONTROL: same while/invariant/decreasing scaffolding as atk_11 but carrying the GOLD value) -> EXIT=0 verifies => the loop machinery is not what rejects atk_6/atk_11.
  prepatch.lean (byte copy of Solution_prepatch.lean) -> EXIT=1 on EXACTLY the 5 clauses refinement.md §B claims (ensures_1,2,4,5,8). PREPATCH BUG REPRODUCED.

### ATTACK LEDGER (exit 1 = rejected; goals = named unsolved obligations):
atk_1  prepatch bug re-encoded (zero on every non-some-true)     ensures_1,2,4(,5,8) atk_2  BOUNDARY: indicator-verdict polarity swapped              ensures_3,4 atk_3  MODEL-CORR: ignores indicator verdict, ALWAYS-uneval      ensures_3,4 atk_4  GROUNDING: operand order flipped (coincide j i)           ensures_2 atk_5  PARTIAL-DOMAIN: wrong only on slice i.id = 0              ensures_1,2,4,7 atk_6  CONTROL-FLOW-EFFECT: returns the GOLD value on every input but DIVERGES on exactly the doubly-unsettled case (the F2P input) -> rejected on `decreasing_1: spin`.

Total-correctness scope kills divergence, so a verifying impl cannot refine to a patch that hangs on the F2P input. atk_7  UNGROUNDED-ORACLE ECHO: always the indicator, ignores both verdicts  ensures_3,4,6,7 atk_8  MODEL-CORR: the two verdicts' ROLES swapped (outer reads kd, inner reads eq) -- agrees with gold wherever the verdicts agree, so it is refuted only on the POPULATED cross-class  ensures_6,7,8 atk_9  VACUITY CONTROL: discriminating branch dead behind infeasible guard `i.id < i.id` -> does NOT go vacuous  ensures_1,2 atk_10 BOUNDARY: definitely-distinct comparison handed to the indicator anyway  ensures_6 atk_11 CONTROL-FLOW: terminating loop-carried accumulator laundering the zero-collapse  ensures_1,2,3,4,6 + invariant_1 atk_12 GROUNDING: indicator over the WRONG operand pair (i,i)   ensures_2 atk_14/15/16 DEMONIC-CHOICE class -- REPORTED HONESTLY AS FAIL-CLOSED, NOT AS SEMANTIC REJECTIONS.

All three (incl. atk_16, which pins the choice to EXACTLY the gold value as the control) die on `failed to synthesize Findable fun v =>...` + `Failed to parse an assertion without names: WPGen sorry`. MatEntry has no Findable instance (Loom/MonadAlgebras/NonDetT/Findable.lean requires Encodable+DecidablePred or FinEnum+DecidablePred), so pickSuchThat/havoc is structurally UNAVAILABLE on this carrier. Because the gold-pinned control fails identically, these three prove only that the evasion fails closed -- they are NOT evidence the spec rejected a weaker predicate. The 12 semantic attacks (>= 5 floor) carry the verdict on their own.

A-LEG AUDIT (my assignment's focus; G-CONF covers R/I). Zero module-level axioms => the A-legs are A-reference only: A2 (eq = real three-valued Eq verdict), A5 (kd = KroneckerDelta's OWN self-evaluation), A6 (fall-through = the value KroneckerDelta(i,j) DENOTES). Re-derived INDEPENDENTLY against real sympy in my own fresh worktree repo_gold (base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b, `git apply patch.diff` => PATCH APPLIED CLEAN; py3.10 collections.abc shim inline):
  - aleg.py:  441 index pairs, transliterated entryFor/coincideValue through mapping.md §2's bijection vs oracle Identity(n).`_entry`(a,b) => 0 DISAGREEMENTS. Classes populated: (True,True)=29, (False,False)=44, (None,None)=360, (None,False)=8.
  - aleg2.py: broadened pool (below/above_fermi, positive/negative/zero/nonzero/even/odd, Rationals, sums, n-1, 3n) 1089 pairs => 0 DISAGREEMENTS. Exactly FOUR verdict classes are realizable: (True,True), (False,False), (None,None), (None,False). The impossible class (some true, kd != some true) never occurs, so the model carries no dead correspondence.
  - The (None,False) CROSS-CLASS IS REAL, not assumed empty: p=Symbol('p',below_fermi=True), q=Symbol('q',above_fermi=True) gives threeval=None, kdval=False, real `_entry`(p,q) = 0, model = 0. This is precisely why the model needs a SECOND verdict; the one-verdict simplification (atk_3) is unfaithful here and the spec rejects it (ensures_3). A5/A6 correspondence holds where it is load-bearing.

refinement.md AUDIT: legs A1-A6 tagged R / R+A-reference(input) / I(R on leaf) / A-reference+I -- no A-consumed (consistent with zero axioms) and NO kind-3; §C's no-kind-3 claim is accurate. Load-bearing prose claims spot-checked BY EXECUTION, not read: (a) §C/§5's Piecewise claim CONFIRMED -- piecewise_probe.py shows Piecewise((1,Eq(i,j)),(0,True)) has flat sum 3 but nested sum does NOT reduce (leaves `Piecewise((3, Eq(i,0)),...) +...`), F2P-PASS=False, while gold KroneckerDelta(i,j) gives !=0 True, flat 3, nested 3, F2P-PASS=True; (b) §B's five named unsolved goals match prepatch.lean's measured output exactly; (c) §A's hunk quote matches patch.diff verbatim and the two import-placement changes are correctly called out as behavioural no-ops outside the modeled site.

### RESOLVE LANE (EXECUTED via harness.run_resolve, docker oracle live; resolve_many.py):
  - patch_gold.diff  -> resolved=True, completed=True, attempts=1  (G-RESOLVE anchor reproduced; lane calibrated, so the flip result below is trustworthy)
  - patch_flip.diff (`return KroneckerDelta(j, i)`, the atk_4 shape the spec REJECTS) -> resolved=True, completed=True, attempts=1  (over-pinning note; resolve-but-not-verify, direction stricter)
No attack verified, so there was no faithful wrong-impl patch to resolve -- the BROKEN trigger never occurred.

**VERDICT:** SOUND. 12 semantic same-spec admissible attacks (>= 5 floor) plus 3 honestly-labelled fail-closed ones all REJECTED; positive control verifies under both the frozen and a strictly stronger tactic; loop-scaffolding and vacuity controls both behave correctly; prepatch reproduced on exactly the documented clauses; A-reference legs re-derived against real sympy with 0/1089 disagreements including the populated cross-class; and the no-counterexample claim is backed by a machine-checked Lean functionality theorem rather than by exhaustion. verify=>correct is not refuted for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled site: Identity.`_entry`(i,j) in sympy/matrices/expressions/matexpr.py (post-patch, per the harness rule that patch.diff is APPLIED for the reference). Reference used: /testbed inside swebench/sweb.eval.x86_64.sympy_1776_sympy-12419 with patch.diff applied (git apply APPLIED, hunks confirmed by sed of lines 476-490).

**SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend()) == True. spec_view printed and inspected: the 8 `ensures` clauses, the pure region (Idx / MatEntry / coincideValue / entryFor + 8 grind lemmas), empty pre/post regions. Impl and proof regions are elided in the spec view, so the contract is exactly the two-stage three-valued selection.

**LEAN:** scripts/lean_verify.sh Solution.lean -> EXIT=0. Solution_prepatch.lean FAILS on precisely the 5 discriminating goals refinement.md §B claims (ensures_1 out != null, ensures_2 out = coincide i j, ensures_4 kd=some true -> unit, ensures_5 out = coincideValue, ensures_8 out = entryFor). G-DIFF discriminator is real, not vacuous.

BUNDLE CHECKS REPRODUCED IN-CONTAINER (patched): axiom_check.py exit 0 (20237 checks); conformance_check.py exit 0 (100008 configs, 0 disagreements).

### MY OWN INDEPENDENT REFUTATION ATTEMPTS (all against the REAL patched callee, not the bundle's shadow; three seeds independent of the bundle's pinned SEED=12419):
1. Exhaustive 41x41 product over an exotic atom pool (symbols w/ integer/real/even/odd/prime/below_fermi/above_fermi assumptions, Integers, Rational, Float, oo, -oo, nan, zoo, I, pi, sqrt(2), E, Dummy, non-commutative Symbol, BooleanAtoms, affine/Abs/sin/Mod/floor compounds, MatrixSymbol element, Piecewise): 1681 pairs, VALUE MISMATCHES = 0.
2. Independent fuzz seed=987654321, depth-2 expression builder, 60000 pairs: 0 mismatches, 0 skips.
3. Independent fuzz seed=31337, depth-3 builder, 39811 tested / 189 raised: 0 mismatches.
Total ~100k inputs on seeds the bundle does not pin. Comparison used the library's structural Basic.`__eq__` — the same relation test_Identity's asserts rest on — with the Lean output mapped into the library per mapping.md §2 (unit->S.One, null->S.Zero, coincide i j -> KroneckerDelta(i,j)).

TOO-STRONG HUNT (the specific faithfulness-break lane). The spec's only non-trivial commitment is the eq=none branch, and the risk is that it over-commits. I enumerated the four (eq,kd) CROSS classes where the two verdicts DISAGREE and confirmed each is POPULATED with 0 mismatches: eq=False,kd=None  n=140  witness (i, oo)      spec=0  real=0 eq=None,kd=False n=56   witness (i, nc)      spec=0  real=0 eq=True,kd=False n=2    witness (oo, -oo)    spec=1  real=1 eq=True,kd=None  n=7    witness (oo, oo)     spec=1  real=1 The eq=True/kd=False class is the decisive one: it proves the spec's OUTER-branch-first ordering matches the patch.

A spec that consulted the indicator first would return 0 on (oo,-oo) where the real `_entry` returns 1 — the spec correctly does not, because `ensures eq = some true -> out = unit` is unconditional in kd. Symmetrically, mapping.md §3.1's claim that the indicator's rules are BROADER than Eq's is measured, not assumed: eq=None,kd=False is populated (below_fermi/above_fermi pair bf/af gives real `_entry` = 0, and non-commutative nc likewise), so the clause `eq=none -> kd=some false -> out = null` is required rather than over-strong. The strictly-stronger neighbour (always-unevaluated indicator on every eq=none) is genuinely refuted by that class.

SCOPE OF ensures_1 (out != null) CHECKED: it is guarded by eq=none AND kd=none, i.e. asserted only where the indicator itself declines to collapse. On 25522+45629 doubly-unsettled samples the real result was an unevaluated KroneckerDelta in 100% of cases (unsettled-but-real-not-KD = 0), never S.Zero. So the non-null claim is not too strong.

ARGUMENT-ORDER (my strongest candidate defect, investigated and DISMISSED): KroneckerDelta.eval canonicalizes operand order via default_sort_key (tensor_functions.py, `if i is not min(i, j, key=default_sort_key): return cls(j, i)`), so real `_entry`(i, bf) returns KroneckerDelta(bf, i) with args SWAPPED relative to (i,j). Raw arg-tuple comparison flagged 448 such pairs (census: same=331, swapped=331, other=0). This is NOT a divergence: the Lean carrier `MatEntry.coincide a b` maps to "an unevaluated KroneckerDelta over the operands", and under the library's own structural equality KroneckerDelta(x,y) == KroneckerDelta(y,x) for 100% of the pool (structural asymmetries = 0, hash differences = 0). The library object is order-insensitive, so `coincide i j` and `coincide j i` denote the same library value; the arg-set check (KD arg-set != {x,y}) returned 0. No observable consequence, and none for the F2P assertions.

**OTHER ANGLES CLOSED:** Eq never returned a non-sympy bool (0 cases). Inputs where `_entry`'s body raises (BooleanAtom/nan/zoo/I) are all UNREACHABLE through the real dispatch — MatrixExpr.`__getitem__` gates on valid_index, and dispatch-reachable-inputs-where-the-body-raises = 0, so the spec's totality (no preconditions) is not overclaiming on any reachable input. Under `with evaluate(False)` shadow and real still agree on (i,i), (i,j), (2,3). (eq=none, kd=some true) has 0 witnesses across ~100k inputs, so that clause is vacuous-but-harmless (it is implied: kd=true requires diff.is_zero, which forces Eq to S.true), not unfaithful.

F2P CONFIRMED end-to-end: base gives In[i,j] = 0, `!=0` False, double sum 0; patched gives KroneckerDelta(i,j), `!=0` True, double sum 3 — exactly the value the spec pins on the doubly-unsettled case.

**CONCLUSION:** no input on which the modeled function disagrees with the real patched callee. The spec is not too strong (every clause is witnessed by a populated class, including all four verdict-disagreement cross-classes) and does not drift from repo behavior. No divergence found.

**Modeled site:** Identity.`_entry`(i,j) in sympy/matrices/expressions/matexpr.py (post-patch, per the harness rule that patch.diff is APPLIED for the reference). Reference used: /testbed inside swebench/sweb.eval.x86_64.sympy_1776_sympy-12419 with patch.diff applied (git apply APPLIED, hunks confirmed by sed of lines 476-490).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** VERDICT: NO-LEAKAGE on the SHIPPED spec view (Solution.lean sha cb88e0b3...). This bundle was REPAIRED after a prior LEAKAGE finding, and the repair is genuine — that is the central fact of this review, so I document it as a measurement rather than taking either the old fail or the new pass on faith.

**NO RELAXATION IN THIS BUNDLE.** There is no RELAXED_LEAKAGE.md (find -iname '*RELAX*' over the instance dir = zero hits) and meta.json has no relaxed_leakage key (checked: absent from the top-level key list; meta.leakage = {status: 'clean'}; gates['G-LEAK'].status = 'pass', not 'relaxed'). So there was no unavoidability argument to inherit or re-derive. I judged the spec view directly on its own merits.

**NO FILE ADDRESSED ME.** I ran leakage.reviewer_directed over every bundle file (Solution.lean, Solution_prepatch.lean, axiom_check.py, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md, patch.diff) -> all clean, zero hits. meta.json/verdict.md mention 'G-PANEL-3' only as gate names in status records, which is legitimate bookkeeping. NOTE FOR THE RECORD: verdict.md DOES retain a prior round's full G-PANEL-3 LEAKAGE writeup ending 'VERDICT: LEAKAGE (bug->fix MECHANISM narration...)'. I treated that as retained evidence about a SUPERSEDED artifact, not as a disposition to echo — per my own standing note, re-judging a retained attack label as the reject lane invents spec weakness. I re-derived against the file actually on disk.

THE REPAIR, MEASURED. The prior fail was stamped against Solution.lean sha 575b553c...; the shipped file is cb88e0b3... I checked each phrase the prior finding cited as leaking and every one is GONE from the current view: 'made the total sum vanish', 'the issue turns on', 'answering it with the zero', 'collapsing to nothing', 'never the zero' -> all absent. Broader sweep over the rendered view for history/diagnosis vocabulary: bug, fix, patch, diagnos, root cause, previously, used to, regression, incorrect, wrong, broken, issue, symptom, vanish, total sum, summation, off-diagonal, 'not known if' -> ALL ABSENT. I also diffed the shipped file against the prior attacker's own de-narrated Solution.lean: the shipped version is a FURTHER-cleaned descendant of it (e.g. 'never the zero' rewritten to 'a symbolic object distinct from the zero'; 'unchanged primitive' -> 'separate primitive'; the 'difference is load-bearing' aside dropped). The repair went past what the prior attacker demanded.

SPEC REGION / VIEW PROVENANCE. markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True — spec regions byte-identical, so the prepatch control exercises the identical contract. Recomputed markers.region_hashes(Solution.lean) spec_view = d6a8d7777ed1a4db070cb8ee219da1f7e48815c7cf036a82a45d78fd06e3b0e7, which MATCHES gates.G-HYGIENE.data.region_hashes exactly. The only diff between the two files is inside impl-start/impl-end, and the 'PRE-PATCH BUG:... two-valued... silently lumped into the else' comment lives in Solution_prepatch.lean's ELIDED impl region (confirmed it does not reach the rendered view).

**GOLD-EDIT TOKENS ABSENT FROM THE VIEW.** The view names no repo symbol: no KroneckerDelta/Kronecker/delta, no Eq(/S.true/S.false/S.One/S.Zero, no Piecewise, no `_entry`, no matexpr/sympy/MatrixSymbol, no fermi/is_zero/fuzzy, no orthogonal/refine. Cross-checked mechanically: of all identifiers on +/- lines of the gold patch, the only ones appearing anywhere in Solution.lean are the generic Lean/English tokens Symbol, else, false, from, import, return, true. 'Identity' occurs only inside the method name identityEntry, and 'identity matrix'/'elements' are PUBLIC domain vocabulary from the problem_statement title itself.

DISCRIMINATOR IS NOT PROBLEM_STATEMENT-DERIVABLE — AND THE VIEW DOESN'T SUPPLY IT EITHER. The public statement gives only the SYMPTOM (double sum prints 0 where n expected, element-wise/diagonal queries fine). Measured term-by-term across problem_statement vs hints_text: kroneckerdelta/kronecker/delta/eq(/piecewise/`_entry`/'not known'/'off-diagonal'/'not evaluating' are ALL False in problem_statement and True in hints_text. So the hints-only causal chain is genuinely non-public — which is exactly why the prior round's narration of it was a leak. The current view reconstructs none of it: it states the abstract desired behaviour positively (a settled comparison yields the unit or the zero; an unsettled one takes the value the coincidence indicator denotes) in de-KroneckerDelta'd wording, never naming the edit, the old value's mistake, or the symptom. That is spec_guide.md directive 6 satisfied ('State the abstract desired behavior; never the edit or the diagnosis'), not violated.

WHAT I DELIBERATELY DID NOT CALL A LEAK, AND WHY. (a) The two-verdict (eq, kd) shape and the 'coincidence indicator' carrier are FAITHFULNESS-FORCED, not gratuitous: mapping.md 3.1 documents a populated below_fermi/above_fermi class where the comparison is unsettled but the real post-patch `_entry` returns S.Zero, so a one-verdict always-unevaluated model would be UNFAITHFUL there. My own G-AX re-run confirms that cross-class is populated, not assumed empty. Stating the required behaviour abstractly is what makes it a spec at all. (b) The identifiers entryFor/MatEntry/identityEntry: leakage.`_patch_changed_symbols`(gold_patch) = {'conjugate','eval_derivative'} and `_patch_new_symbols` = set(), because the patch rewrites `_entry`'s BODY so `def _entry` appears only as a CONTEXT line and 'entry' is never screened. I checked this rather than assuming, and I am NOT reporting it — 'entry'/'element' sits inside the public statement's own vocabulary ('elements of an identity matrix'), so flagging it would be a lexer artifact, not a disclosure.

CORE GATES RE-RUN BY ME, NOT INHERITED (all leakage-relevant gates are stamped against the CURRENT sha cb88e0b3: G-LEAK, G-AX, G-CONF, G-DIFF, G-GOLD, G-HYGIENE, G-INTEGRITY, G-MUT, G-PBT, G-VERIFY all CURRENT).
  - lean_verify.sh Solution.lean -> exit 0 (G-VERIFY/G-GOLD reproduce).
  - lean_verify.sh Solution_prepatch.lean -> exit 1 on exactly ensures_1,2,4,5,8 (G-DIFF reproduces, matching refinement.md B verbatim).
  - G-CONF in the instance container with the gold patch applied -> rc=0, '100008 index-pair configurations, 0 disagreements'. Verified the patch really applied and the base commit is 479939f8c6 by reading the patched `_entry` source out of the worktree.
  - G-CONF NEGATIVE CONTROL against UNPATCHED base -> rc=1 with 5 concrete disagreements (e.g. i=i j=j shadow=KroneckerDelta(i,j) oracle=0). The oracle is real, not a no-op that would pass anything.
  - G-AX -> rc=0, '20237 index-pair checks incl. boundary, the populated Eq-unsettled/indicator-distinct cross-class, and 20000 fuzz, 0 disagreements'.
  - leakage.screen(Solution.lean, VelvetBackend, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. I did not lean on this screen as a disposition (the prior round showed its narration word-list has synonym blind spots); the semantic sweep and the strip test above are my actual basis.

BOOKKEEPING DEFECT (recorded, does NOT change my verdict). meta.json's TOP-LEVEL region_hashes block is STALE — it still holds the pre-repair values (spec_view 4b4b341c...) while the true current spec_view is d6a8d777... The authoritative per-gate copy under gates.G-HYGIENE.data.region_hashes is correct and current, and every leakage-relevant gate is stamped against the shipped sha, so the staleness is a cosmetic duplicate-field lag rather than an unsound stamp. Separately, gates G-EQ, G-PANEL, G-PANEL-1/2/3 remain stamped against the superseded 575b553c and should be re-run for the shipped artifact; the retained G-PANEL-3 'fail' in particular no longer describes any file in this bundle. Flagging for the release gate — greenness is green_check.classify's call, not mine.

**BOTTOM LINE:** the spec view discloses nothing about the gold edit beyond the public problem_statement. The prior leak was real and has been genuinely de-narrated; my total-comment-strip test shows the remaining prose carries no discriminating power at all, so there is no residual disclosure to find.

Counterexample / evidence:

```
Not applicable — this is the leakage leg, so there is no same-spec verifying rival. My machine evidence is a strip-and-reverify (avoidability) construction  showing that ALL prose in the current spec view is non-load-bearing, i.e. the discriminating power lives entirely in the `ensures` clauses:

I stripped EVERY comment from the shipped pair — all /- ... -/ block comments and all `--` line comments except the region markers (a strictly more aggressive de-narration than the prior round's three-block edit). Confirmed clause lists byte-identical (Solution.lean 44/44, Solution_prepatch.lean 39/39) and same_spec(stripped, stripped_prepatch) = True.

  lean_verify.sh Solution.lean           -> exit 0 (gold impl still VERIFIES)
  lean_verify.sh Solution_prepatch.lean  -> exit 1 (pre-patch impl still REJECTED)

Prepatch rejection is on exactly the five documented discriminating goals, unchanged by total comment removal:
  ensures_1: eq = none -> kd = none -> out != MatEntry.null
  ensures_2: eq = none -> kd = none -> out = MatEntry.coincide i j
  ensures_4: eq = none -> kd = some true -> out = MatEntry.unit
  ensures_5: eq = none -> out = coincideValue i j kd
  ensures_8: out = entryFor i j eq kd

Crucially, this cuts the OPPOSITE way from the prior round: with zero prose the spec is fully discriminating AND the shipped prose contains no bug->fix narration to strip. There is nothing left to remove that would change the disclosure, because nothing disclosing remains.
```

**VERDICT:** NO-LEAKAGE on the SHIPPED spec view (Solution.lean sha cb88e0b3...). This bundle was REPAIRED after a prior LEAKAGE finding, and the repair is genuine — that is the central fact of this review, so I document it as a measurement rather than taking either the old fail or the new pass on faith.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.