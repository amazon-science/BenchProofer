# P2 adversarial audit — django__django-15503

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12bc.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_13bc.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition is a TOTAL FUNCTIONAL EQUALITY (result = lhsJsonPath ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))) universally quantified over byName : Bool, so it pins the assembled path pointwise on the whole precondition domain (keys != []) AND pins BOTH final-key rendering forms. The only degree of freedom left is behavior at keys = [], which the precondition excludes; two attacks (atk_8, atk_13bc) exploited exactly that and both closed with clean axioms, but their faithful patches BOTH RESOLVE under the official harness (Python's rhs_key_transforms is always non-empty, so the exploited branch is unreachable dead code). Hence no verify-but-not-resolve pair exists: verify => correct holds.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,10 +144,9 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
-  let intermediate := keys.dropLast
-  let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
+  -- pre-patch base_commit code: the ENTIRE key list, final key included, is
+  -- routed through compile_json_path (pathOfKeys); byName never consulted.
+  let rhsJsonPath := pathOfKeys keys
   return lhsJsonPath ++ rhsJsonPath
 -- impl-end
 
@@ -157,7 +156,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,10 +144,12 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- hardwires compile_json_path_final_key = ".%s" % json.dumps(k) for EVERY
+  -- caller; the HasKeyOrArrayIndex override (byName=false) is dropped.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
   let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
+  rhsJsonPath := rhsJsonPath ++ memberSegment finalKey
   return lhsJsonPath ++ rhsJsonPath
 -- impl-end
 
@@ -157,7 +159,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,10 +144,12 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- restructured like the patch (dropLast/getLast split) but the final key is
+  -- still rendered positionally: compile_json_path_final_key = compile_json_path([k]).
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
   let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
+  rhsJsonPath := rhsJsonPath ++ renderSegment finalKey
   return lhsJsonPath ++ rhsJsonPath
 -- impl-end
 
@@ -157,7 +159,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,15 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- partial domain: applies the fix only when there is at least one
+  -- intermediate step; a single-element rhs_key_transforms (the common
+  -- has_key='1111' case) falls back to the pre-patch positional rendering.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  if intermediate.isEmpty then
+    return lhsJsonPath ++ renderSegment finalKey
+  else
+    return lhsJsonPath ++ (pathOfKeys intermediate ++ finalSegment byName finalKey)
 -- impl-end
 
 -- proof-start
@@ -157,7 +161,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,9 +144,10 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
-  let intermediate := keys.dropLast
+  -- boundary/off-by-one: forgets the starred-unpack truncation, so the final key
+  -- is emitted twice (once positionally by compile_json_path, once by name).
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
+  let mut rhsJsonPath := pathOfKeys keys
   rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
   return lhsJsonPath ++ rhsJsonPath
 -- impl-end
@@ -157,7 +158,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,10 +144,12 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- control-flow effect: the mutable accumulator is built in the wrong order,
+  -- so the final-key segment is prepended to the intermediate path.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
+  let mut rhsJsonPath := finalSegment byName finalKey
+  rhsJsonPath := rhsJsonPath ++ pathOfKeys intermediate
   return lhsJsonPath ++ rhsJsonPath
 -- impl-end
 
@@ -157,7 +159,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,15 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- ungrounded oracle echo: hardwires exactly the key texts the FAIL_TO_PASS
+  -- fixtures use ("1111" from test_has_key_number, and the test_has_keys
+  -- digit keys) and leaves every other key on the pre-patch path.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  let oracleKeys : List String := ["1111", "1", "111", "0", "2", "3"]
+  let fin := if oracleKeys.contains finalKey then memberSegment finalKey
+             else renderSegment finalKey
+  return lhsJsonPath ++ (pathOfKeys intermediate ++ fin)
 -- impl-end
 
 -- proof-start
@@ -157,7 +161,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -144,6 +144,11 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- exploits the ONLY freedom an exact-equality postcondition leaves: the
+  -- precondition keys ≠ [] excludes the empty list, so any behavior there is
+  -- unconstrained. Emits a bogus sentinel path for keys = [].
+  if keys.isEmpty then
+    return "$.__SBU_AUDIT_SENTINEL__"
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
   let mut rhsJsonPath := pathOfKeys intermediate
@@ -157,7 +162,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,16 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
-  let intermediate := keys.dropLast
-  let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  -- restructures the split via take/reverse-head instead of dropLast/getLastD
+  -- (extensionally identical on keys ≠ []) AND drops the lhs prefix entirely
+  -- when keys = [], which the precondition never reaches.
+  match keys.reverse with
+  | [] => return ""
+  | finalKey :: revInit =>
+    let intermediate := revInit.reverse
+    let mut rhsJsonPath := pathOfKeys intermediate
+    rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
+    return lhsJsonPath ++ rhsJsonPath
 -- impl-end
 
 -- proof-start
@@ -157,7 +162,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => simp at h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,19 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- A-reference attack: replaces the deep int()-parse model with the NAIVE
+  -- "every char is an ASCII 0-9 digit" test that mapping.md explicitly says is
+  -- what the fix "really cares about". Diverges from int() on "-1", "+2",
+  -- " 3 ", "1_0", and non-ASCII-script digits.
+  let naiveNum (k : String) : Bool := !k.isEmpty && k.toList.all (fun c => '0' ≤ c && c ≤ '9')
+  let seg (k : String) : String :=
+    if naiveNum k then "[" ++ toString ((k.toList.foldl (fun a d => a*10 + (d.toNat - 48)) 0 : Nat)) ++ "]"
+    else memberSegment k
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  let mut rhs := String.join (intermediate.map seg)
+  rhs := rhs ++ (if byName then memberSegment finalKey else seg finalKey)
+  return lhsJsonPath ++ rhs
 -- impl-end
 
 -- proof-start
@@ -157,7 +165,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => exact absurd rfl h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, Id.run, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,19 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- boundary attack on the deep model: drops the 4300-digit parse budget, so a
+  -- 4301-digit key is rendered positionally instead of as a named member.
+  let bigNum (k : String) : Option Int :=
+    let cs := stripSpace k.toList
+    if !cs.isEmpty && cs.all isDecimalDigit then
+      some (Int.ofNat (cs.foldl (fun a d => a*10 + (digitValue d).getD 0) 0))
+    else none
+  let seg (k : String) : String :=
+    match bigNum k with | some n => "[" ++ toString n ++ "]" | none => memberSegment k
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  return lhsJsonPath ++ (String.join (intermediate.map seg)
+    ++ (if byName then memberSegment finalKey else seg finalKey))
 -- impl-end
 
 -- proof-start
@@ -157,7 +165,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => exact absurd rfl h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, Id.run, List.dropLast]
+    | aesop
 -- proof-end
```

Attack 12 — `atk_12bc.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,13 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
-  let intermediate := keys.dropLast
-  let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  -- second empty-list exploit, reached by a reverse-match split that is
+  -- extensionally identical to dropLast/getLastD on keys != []; the keys = []
+  -- branch drops the lhs prefix and emits a bogus root path.
+  match keys.reverse with
+  | [] => return "$[999]"
+  | finalKey :: revInit =>
+    return lhsJsonPath ++ (pathOfKeys revInit.reverse ++ finalSegment byName finalKey)
 -- impl-end
 
 -- proof-start
@@ -157,7 +159,17 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  rcases List.eq_nil_or_concat keys with rfl | ⟨ys, y, rfl⟩
+  · exact absurd rfl h
+  · have hg : (ys.concat y).getLastD "" = y := by
+      simp [List.concat_eq_append, List.getLastD_eq_getLast?, List.getLast?_append]
+    have hd : (ys.concat y).dropLast = ys := by simp [List.concat_eq_append]
+    simp only [List.concat_eq_append, List.reverse_append, List.reverse_cons,
+               List.reverse_nil, List.nil_append, List.cons_append,
+               List.reverse_reverse, Id.run, pure]
+    rw [hd, hg] at *
+    simp [List.concat_eq_append] at hd hg ⊢
+    rfl
 -- proof-end
```

Attack 13 — `atk_13bc.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -144,11 +144,17 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- provably-equal restructure: a NON-numeric final key is sent to the
+  -- named-member renderer regardless of byName (sound because renderSegment k =
+  -- memberSegment k exactly when numericKey k = none). The byName selector is
+  -- therefore consulted only for numeric-looking keys.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  let fin :=
+    match numericKey finalKey with
+    | none   => memberSegment finalKey
+    | some n => if byName then memberSegment finalKey else "[" ++ toString n ++ "]"
+  return lhsJsonPath ++ (pathOfKeys intermediate ++ fin)
 -- impl-end
 
 -- proof-start
@@ -159,5 +165,7 @@
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
   intro byName lhsJsonPath keys _
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  simp only [Id.run, finalSegment, renderSegment]
+  cases hb : byName <;> cases hn : numericKey (keys.getLastD "") <;>
+    simp only [hb, hn, Id.run, pure, memberSegment, List.getLastD] <;> rfl
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,11 +144,11 @@
 -- impl-start
 def implementation_keyLookupPath
     (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
+  -- selector inverted: HasKeyLookup gets the array-index rendering and
+  -- HasKeyOrArrayIndex gets the named-member rendering.
   let intermediate := keys.dropLast
   let finalKey := keys.getLastD ""
-  let mut rhsJsonPath := pathOfKeys intermediate
-  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
-  return lhsJsonPath ++ rhsJsonPath
+  return lhsJsonPath ++ (pathOfKeys intermediate ++ finalSegment (!byName) finalKey)
 -- impl-end
 
 -- proof-start
@@ -157,7 +157,13 @@
       keys ≠ [] →
       problem_spec_keyLookupPath byName lhsJsonPath keys
         (implementation_keyLookupPath byName lhsJsonPath keys) := by
-  intro byName lhsJsonPath keys _
+  intro byName lhsJsonPath keys h
   unfold problem_spec_keyLookupPath implementation_keyLookupPath
-  rfl
+  first
+    | rfl
+    | (cases keys with
+       | nil => exact absurd rfl h
+       | cons a t => cases byName <;> simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment])
+    | simp_all [pathOfKeys, finalSegment, renderSegment, memberSegment, Id.run, List.dropLast]
+    | aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the database JSON-path expression that locates a key inside a JSON
document, for a key-existence query on a JSON field.

The expression is assembled from a left-hand path prefix and a non-empty list of
right-hand key steps. Each intermediate step descends into the document by the
given step. A step whose text reads as a base-10 integer (decimal digits in any
script) denotes an addressable positional step; every other step denotes a named
member of the enclosing object.

The FINAL step is addressed in one of TWO forms, and which one applies is a
property of the enquiry being assembled rather than of the step text. Some
enquiries ask whether the document carries a MEMBER OF A GIVEN NAME, and for
those the final step must be addressed by member name whatever its text happens
to read as. Other enquiries ask about whichever location the step text denotes,
and for those the final step is addressed exactly like an intermediate one. Both
forms must therefore be available from the same assembly, selected by the caller;
neither may be assumed.

Keys are modeled as `String`; the assembled path is a `String`; the selection of
the final step's addressing form is modeled as a `Bool` input.
-/

-- axioms-start
/-- Encoder that renders a key as a quoted path token (a standard JSON string
serializer). Its exact escaping is irrelevant here — it is applied identically
wherever a key is addressed by name — so it is kept as an opaque callee. -/
opaque encodeKey : String → String
-- axioms-end

-- pure-start
/-- The whitespace a base-10 integer parse tolerates around the text it reads:
the ASCII control/space run, next line, and the Unicode space separators
(including the line and paragraph separators). -/
def isParseSpace (c : Char) : Bool :=
  (0x09 ≤ c.toNat && c.toNat ≤ 0x0d)
    || c.toNat = 0x20 || c.toNat = 0x85 || c.toNat = 0xa0 || c.toNat = 0x1680
    || (0x2000 ≤ c.toNat && c.toNat ≤ 0x200a)
    || c.toNat = 0x2028 || c.toNat = 0x2029 || c.toNat = 0x202f
    || c.toNat = 0x205f || c.toNat = 0x3000

/-- Trim leading and trailing parse-whitespace. -/
def stripSpace (cs : List Char) : List Char :=
  ((cs.dropWhile isParseSpace).reverse.dropWhile isParseSpace).reverse

/-- The first code point of each contiguous block of ten decimal digits. A
base-10 parse reads a digit from ANY script, not only the ASCII block, so a
digit is a character lying within nine of one of these zeros. -/
def digitZeros : List Nat :=
  [0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6,
   0xc66, 0xce6, 0xd66, 0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0,
   0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50,
   0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0,
   0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0,
   0x11650, 0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0,
   0x16a60, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140,
   0x1e2f0, 0x1e950, 0x1fbf0]

/-- The base-10 value of a character that is a decimal digit, in whatever
script it is written; `none` if it is not a decimal digit. -/
def digitValue (c : Char) : Option Nat :=
  (digitZeros.find? (fun z => z ≤ c.toNat && c.toNat ≤ z + 9)).map (fun z => c.toNat - z)

/-- Whether a character reads as a base-10 digit. -/
def isDecimalDigit (c : Char) : Bool := (digitValue c).isSome

/-- The greatest number of decimal digits a base-10 parse will read out of one
step text. A text carrying more digits than this does not yield a value at all,
so it is not positional and is addressed by member name like any other text. -/
def maxParseDigits : Nat := 4300

/-- A valid base-10 magnitude: a non-empty run of digits, optionally with
single underscores used strictly as separators between digits (no leading,
trailing, or doubled underscore), whose digits stay inside the parse's digit
budget. -/
def validNumBody (cs : List Char) : Bool :=
  !cs.isEmpty
    && cs.all (fun c => isDecimalDigit c || c = '_')
    && (cs.head?.map isDecimalDigit |>.getD false)
    && (cs.getLast?.map isDecimalDigit |>.getD false)
    && (cs.zip cs.tail).all (fun p => !(p.1 = '_' && p.2 = '_'))
    && (cs.filter isDecimalDigit).length ≤ maxParseDigits

/-- A step text is *positional* iff, after trimming surrounding whitespace and an
optional leading sign, it is a valid base-10 magnitude (digits with underscore
separators); in that case this returns its integer value. This mirrors a base-10
integer parse of the step text. -/
def numericKey (s : String) : Option Int :=
  let cs0 := stripSpace s.toList
  match cs0 with
  | [] => none
  | c :: rest =>
    let (sign, body) := if c = '-' then ((-1 : Int), rest)
                        else if c = '+' then ((1 : Int), rest)
                        else ((1 : Int), cs0)
    if validNumBody body then
      some (sign * Int.ofNat ((body.filter (· ≠ '_')).foldl
        (fun a d => a * 10 + (digitValue d).getD 0) 0))
    else none

/-- Address a step as a NAMED MEMBER of the enclosing object: the member-access
form, carrying the step text rendered as a quoted path token. -/
def memberSegment (k : String) : String :=
  "." ++ encodeKey k

/-- Address a step by WHAT ITS TEXT DENOTES: a text that reads as a base-10
integer becomes the bracketed positional step for that value; any other text is
addressed as a named member. -/
def renderSegment (k : String) : String :=
  match numericKey k with
  | some n => "[" ++ toString n ++ "]"
  | none   => memberSegment k

/-- Path text for a list of steps, each addressed by what its text denotes (root
omitted). -/
def pathOfKeys (keys : List String) : String :=
  String.join (keys.map renderSegment)

/-- Address the FINAL step in the form the enquiry selects. When the enquiry is
about a member of a given NAME, the final step is addressed as a named member
whatever its text reads as — in particular a text that reads as an integer is
still addressed by name, not positionally. Otherwise the final step is addressed
by what its text denotes, exactly like an intermediate step. -/
def finalSegment (byName : Bool) (k : String) : String :=
  if byName then memberSegment k else renderSegment k
-- pure-end

-- post-conditions-start
/-- The assembled path is the prefix, followed by the intermediate steps (all
but the last key, each addressed by what its text denotes), followed by the final
key addressed in the form `byName` selects. Both selections are constrained: the
assembly must deliver the named-member form when it is asked for AND the
denoted-location form when THAT is asked for, so neither form may be hardwired. -/
def problem_spec_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String)
    (result : String) : Prop :=
  result = lhsJsonPath
    ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))
-- post-conditions-end

-- impl-start
def implementation_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
  let intermediate := keys.dropLast
  let finalKey := keys.getLastD ""
  let mut rhsJsonPath := pathOfKeys intermediate
  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
  return lhsJsonPath ++ rhsJsonPath
-- impl-end

-- proof-start
theorem correct_keyLookupPath :
    ∀ (byName : Bool) (lhsJsonPath : String) (keys : List String),
      keys ≠ [] →
      problem_spec_keyLookupPath byName lhsJsonPath keys
        (implementation_keyLookupPath byName lhsJsonPath keys) := by
  intro byName lhsJsonPath keys _
  unfold problem_spec_keyLookupPath implementation_keyLookupPath
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — django__django-15503 (lean). Repo worktree at base_commit 859a87d873:; gold-patched copy:.

ALL 19 candidate files pass same_spec == True (axioms/pure/pre/post byte-identical; only the impl+proof regions edited).

### Positive control
pos_control.lean (shipped impl verbatim)
  cmd: bash scripts/lean_verify.sh pos_control.lean -> EXIT 0
  axioms: ax_pos_control.lean (+ '#print axioms correct_keyLookupPath') -> EXIT 0, "'correct_keyLookupPath' does not depend on any axioms" (CLEAN, no sorryAx)

### Prepatch reproduced: yes
atk_1.lean re-encodes the base_commit bug (impl body 'let rhsJsonPath := pathOfKeys keys' — the ENTIRE key list, final key included, routed through compile_json_path; byName never consulted). This is byte-identical in behavior to the shipped Solution_prepatch.lean impl (verified by extracting its impl region).
  cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT 1 (REJECTED)
  residue: 'unsolved goals ... lhsJsonPath ++ String.join (List.map renderSegment keys) = lhsJsonPath ++ (String.join (...).dropLast ++ if byName then "." ++ encodeKey ... else match numericKey ...)' — a genuine spec-discriminating goal, not a syntax error.

=== 14 DISTINCT WRONG IMPLS, ALL VERIFIED-OR-REJECTED (cmd = bash scripts/lean_verify.sh <f>.lean) ===
REJECTED (EXIT 1) — 12; every log's residue is 'error: unsolved goals' on the discriminating equality (confirmed by reading each log; NO parse/elab errors, NO timeouts):
  atk_1  prepatch bug (whole list positional)                                        EXIT 1
  atk_2  hardwires the NAMED form (drops the HasKeyOrArrayIndex byName=false override) EXIT 1
  atk_3  hardwires the DENOTED form (patch restructure but fix absent)               EXIT 1
  atk_4  PARTIAL DOMAIN: fix applied only when >=1 intermediate step; the single-key has_key='1111' case falls back to positional  EXIT 1
  atk_5  BOUNDARY off-by-one: intermediate = whole list, final key emitted twice     EXIT 1
  atk_6  CONTROL-FLOW EFFECT: accumulator built in wrong order (final segment prepended) EXIT 1
  atk_7  UNGROUNDED ORACLE ECHO: special-cases exactly the F2P fixture key texts ["1111","1","111","0","2","3"], pre-patch path otherwise  EXIT 1
  atk_9  reverse-split restructure + drops the lhs prefix at keys = []               EXIT 1
  atk_10 A-REFERENCE ATTACK on the deep model: replaces the int()-parse with a NAIVE ASCII-0-9-only test (diverges on "-1","+2"," 3 ","1_0", non-ASCII digits)  EXIT 1
  atk_11 A-REFERENCE BOUNDARY: drops the 4300-digit maxParseDigits budget, so a 4301-digit key renders positionally  EXIT 1
  atk_12bc keys=[] exploit via reverse-match emitting "$[999]"                        EXIT 1 (see caveat below)
  atk_14 SELECTOR INVERTED: finalSegment (!byName) — the two renderings swapped      EXIT 1

VERIFIED WITH CLEAN AXIOMS (EXIT 0) — 2. Per protocol BOTH had their faithful refined patch materialized and RUN through the official harness:
  atk_8.lean   EXIT 0; axioms (ax_atk_8.lean) = [propext, Quot.sound] — CLEAN, no sorryAx.
    Impl: returns "$.__SBU_AUDIT_SENTINEL__" when keys = [], gold behavior otherwise.
    Faithful patch: atk_8.patch (gold fix + an 'if not rhs_key_transforms: rhs_params.append("$.__SBU_AUDIT_SENTINEL__"); continue' guard). `git apply --check` OK.
    RESOLVE (EXECUTED): run_resolve('django__django-15503', atk_8.patch, run_id='sbu-audit-eq-atk8-1tqxo36b')
      -> resolved=True, completed=True, note='resolved'; patch_successfully_applied=True
      -> FAIL_TO_PASS 2/2 success (test_has_key_number, test_has_keys), 0 failure; PASS_TO_PASS 78/78 success, 0 failure; PASS_TO_FAIL empty.
    => RESOLVES. Not a break.
  atk_13bc.lean EXIT 0; axioms (ax_atk_13bc.lean) = [propext] — CLEAN, no sorryAx.
    Impl: routes a NON-numeric final key to memberSegment regardless of byName (sound in Lean because renderSegment k = memberSegment k exactly when numericKey k = none), consulting byName only for numeric-looking keys.
    Faithful patch: atk_13bc.patch (gold fix + an explicit try int(final_key)/except ValueError branch that emits '.%s' % json.dumps(final_key) directly). `git apply --check` OK.
    RESOLVE (EXECUTED): run_resolve('django__django-15503', atk_13bc.patch, run_id='sbu-audit-eq-atk13bc-1tqxo36b')
      -> resolved=True, completed=True, note='resolved'.
    => RESOLVES. Not a break.
No impl with a closing clean-axiom proof has a non-resolving faithful patch => verify => correct is NOT falsified.

CAVEAT (honest, does not affect the verdict): atk_12/atk_12b/atk_12bc and atk_13/atk_13b are PROVABLY EQUAL to gold on keys != [] (they only restructure the split or the numeric case analysis). Their EXIT 1 results are TACTIC weakness, not spec rejection — the atk_13b residue was literally 'pure X = X' and closed once I added `rfl` (that is atk_13bc, EXIT 0). atk_12bc's residue is likewise reflexive modulo a getLastD/getLast? unfolding I did not finish discharging; I report it as rejected-by-my-tactics rather than claiming the spec rejects it. Since these impls are extensionally identical to gold, closing them could only ever produce another RESOLVING patch (as atk_13bc in fact did), so this cannot hide a break.

### REFINEMENT.MD AUDIT (leg kinds)
refinement.md tags all 5 legs R (#1-#4) / I (#5). NO kind-3 (untagged/unjustified) leg. Confirmed against the real code: #1 keys.dropLast   <-> '*rhs_key_transforms' starred-unpack        R  OK #2 keys.getLastD "" <-> 'final_key' binding                        R  OK (total default unreachable under keys != [], matching Python's guaranteed >=1 element) #3 pathOfKeys intermediate <-> compile_json_path(..., include_root=False)  R  OK #4 finalSegment byName finalKey <-> self.compile_json_path_final_key(final_key)  R  OK — the fixed line #5 lhsJsonPath ++ rhsJsonPath <-> rhs_params.append(lhs_json_path + rhs_json_path)  I  OK A-LEG STATUS: there is NO A-consumed and NO A-reference leg, and this is CORRECT, not an evasion.

The sole callee `encodeKey` (<-> json.dumps) is declared `opaque` (signature only, no axiom, no _prop). I confirmed the proof consumes no property of it: pos_control's `#print axioms` reports NO axiom dependence at all, so nothing about encodeKey is assumed. It is applied identically on named-member steps in ops #3 and #4 and on BOTH sides of the fix, so it cancels. axiom_check.py is a legitimate skip stub (status=skip, 'no consumed axioms in bundle'), consistent with the empty axioms region.

### MODEL <-> PATCH CORRESPONDENCE (the A-leg substitute check I ran instead)
Because the positional-vs-named routing is modeled DEEPLY (numericKey/renderSegment/finalSegment) rather than axiomatized, I differential-tested the deep model against the REAL callees, which is where an A-reference obligation would otherwise bite.

(a) numericKey vs CPython int(): transcribed Solution.lean's isParseSpace/stripSpace/digitZeros/digitValue/validNumBody/numericKey and compared to int() over 60 adversarial texts — digit runs, "-1", "+2", " 3 ", "1_0", "1_", "_1", "1__0", "--1", "+-1", "1.0", "0x10", "1e3", non-ASCII scripts (Arabic-Indic, Bengali, Myanmar, Tibetan, fullwidth, Mathematical Monospace, U+1FBF0), U+2028/U+3000/U+180E/U+200B whitespace edges, and the 4300/4301/5000-digit budget boundary. RESULT: 0 divergences.

(b) FULL ASSEMBLY vs the real patched Python: applied gold.diff to, imported the actual django.db.models.fields.json.compile_json_path, and lifted both real post-patch renderers verbatim (HasKeyLookup.compile_json_path_final_key = '.%s' % json.dumps(k); HasKeyOrArrayIndex.compile_json_path_final_key = compile_json_path([k], include_root=False)). Compared the Lean postcondition against the patched as_sql RHS body over lhsJsonPath in {"$","$.a","$[0]","$.a[3].b"} x key lists of length 1-4 drawn from a 39-symbol adversarial alphabet (digit runs, signed, underscore-separated, whitespace-padded, non-ASCII digits, quote/backslash escapes, the 4301-digit key), for BOTH byName selections, plus exhaustive single- and double-key sweeps. RESULT: 25280 cases compared, 0 DIVERGENCES.

This also confirms the mapping.md byName<->subclass correspondence is real: byName=true is HasKeyLookup/HasKey/HasKeys/HasAnyKeys (the fix), byName=false is the HasKeyOrArrayIndex override that deliberately preserves base behavior for the isnull/oracle path. Both are pinned by the spec's forall byName, so neither can be hardwired — atk_2 and atk_3 (each hardwiring one) are both rejected, and atk_14 (swapping them) is rejected.

### Why the spec holds
The postcondition is an exact string equality fixing the result pointwise over the entire precondition domain and over both Bool selections, so any impl differing anywhere on keys != [] is immediately unprovable. Domain-narrowing (atk_4), boundary (atk_5, atk_11), control-flow-effect (atk_6), oracle-echo (atk_7), hardwired-form (atk_2, atk_3), inverted-selector (atk_14), and shallow-model (atk_10) attacks are all rejected. The residual keys = [] freedom is genuine but unreachable in Python, and both exploits of it resolve.

VERDICT: SOUND. 14 admissible same-spec attacks run (12 rejected, 2 verified with clean axioms), positive control verifies with no axiom dependence, prepatch bug reproduced and rejected, and every verifying attack's faithful patch was materialized and EXECUTED through run_resolve — both resolved (F2P 2/2, P2P 78/78). No verify-but-not-resolve pair exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12bc.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_13bc.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition is a TOTAL FUNCTIONAL EQUALITY (result = lhsJsonPath ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))) universally quantified over byName : Bool, so it pins the assembled path pointwise on the whole precondition domain (keys != []) AND pins BOTH final-key rendering forms. The only degree of freedom left is behavior at keys = [], which the precondition excludes; two attacks (atk_8, atk_13bc) exploited exactly that and both closed with clean axioms, but their faithful patches BOTH RESOLVE under the official harness (Python's rhs_key_transforms is always non-empty, so the exploited branch is unreachable dead code). Hence no verify-but-not-resolve pair exists: verify => correct holds.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12bc.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13bc.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the database JSON-path expression that locates a key inside a JSON
document, for a key-existence query on a JSON field.

The expression is assembled from a left-hand path prefix and a non-empty list of
right-hand key steps. Each intermediate step descends into the document by the
given step. A step whose text reads as a base-10 integer (decimal digits in any
script) denotes an addressable positional step; every other step denotes a named
member of the enclosing object.

The FINAL step is addressed in one of TWO forms, and which one applies is a
property of the enquiry being assembled rather than of the step text. Some
enquiries ask whether the document carries a MEMBER OF A GIVEN NAME, and for
those the final step must be addressed by member name whatever its text happens
to read as. Other enquiries ask about whichever location the step text denotes,
and for those the final step is addressed exactly like an intermediate one. Both
forms must therefore be available from the same assembly, selected by the caller;
neither may be assumed.

Keys are modeled as `String`; the assembled path is a `String`; the selection of
the final step's addressing form is modeled as a `Bool` input.
-/

-- axioms-start
/-- Encoder that renders a key as a quoted path token (a standard JSON string
serializer). Its exact escaping is irrelevant here — it is applied identically
wherever a key is addressed by name — so it is kept as an opaque callee. -/
opaque encodeKey : String → String
-- axioms-end

-- pure-start
/-- The whitespace a base-10 integer parse tolerates around the text it reads:
the ASCII control/space run, next line, and the Unicode space separators
(including the line and paragraph separators). -/
def isParseSpace (c : Char) : Bool :=
  (0x09 ≤ c.toNat && c.toNat ≤ 0x0d)
    || c.toNat = 0x20 || c.toNat = 0x85 || c.toNat = 0xa0 || c.toNat = 0x1680
    || (0x2000 ≤ c.toNat && c.toNat ≤ 0x200a)
    || c.toNat = 0x2028 || c.toNat = 0x2029 || c.toNat = 0x202f
    || c.toNat = 0x205f || c.toNat = 0x3000

/-- Trim leading and trailing parse-whitespace. -/
def stripSpace (cs : List Char) : List Char :=
  ((cs.dropWhile isParseSpace).reverse.dropWhile isParseSpace).reverse

/-- The first code point of each contiguous block of ten decimal digits. A
base-10 parse reads a digit from ANY script, not only the ASCII block, so a
digit is a character lying within nine of one of these zeros. -/
def digitZeros : List Nat :=
  [0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6,
   0xc66, 0xce6, 0xd66, 0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0,
   0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50,
   0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0,
   0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0,
   0x11650, 0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0,
   0x16a60, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140,
   0x1e2f0, 0x1e950, 0x1fbf0]

/-- The base-10 value of a character that is a decimal digit, in whatever
script it is written; `none` if it is not a decimal digit. -/
def digitValue (c : Char) : Option Nat :=
  (digitZeros.find? (fun z => z ≤ c.toNat && c.toNat ≤ z + 9)).map (fun z => c.toNat - z)

/-- Whether a character reads as a base-10 digit. -/
def isDecimalDigit (c : Char) : Bool := (digitValue c).isSome

/-- The greatest number of decimal digits a base-10 parse will read out of one
step text. A text carrying more digits than this does not yield a value at all,
so it is not positional and is addressed by member name like any other text. -/
def maxParseDigits : Nat := 4300

/-- A valid base-10 magnitude: a non-empty run of digits, optionally with
single underscores used strictly as separators between digits (no leading,
trailing, or doubled underscore), whose digits stay inside the parse's digit
budget. -/
def validNumBody (cs : List Char) : Bool :=
  !cs.isEmpty
    && cs.all (fun c => isDecimalDigit c || c = '_')
    && (cs.head?.map isDecimalDigit |>.getD false)
    && (cs.getLast?.map isDecimalDigit |>.getD false)
    && (cs.zip cs.tail).all (fun p => !(p.1 = '_' && p.2 = '_'))
    && (cs.filter isDecimalDigit).length ≤ maxParseDigits

/-- A step text is *positional* iff, after trimming surrounding whitespace and an
optional leading sign, it is a valid base-10 magnitude (digits with underscore
separators); in that case this returns its integer value. This mirrors a base-10
integer parse of the step text. -/
def numericKey (s : String) : Option Int :=
  let cs0 := stripSpace s.toList
  match cs0 with
  | [] => none
  | c :: rest =>
    let (sign, body) := if c = '-' then ((-1 : Int), rest)
                        else if c = '+' then ((1 : Int), rest)
                        else ((1 : Int), cs0)
    if validNumBody body then
      some (sign * Int.ofNat ((body.filter (· ≠ '_')).foldl
        (fun a d => a * 10 + (digitValue d).getD 0) 0))
    else none

/-- Address a step as a NAMED MEMBER of the enclosing object: the member-access
form, carrying the step text rendered as a quoted path token. -/
def memberSegment (k : String) : String :=
  "." ++ encodeKey k

/-- Address a step by WHAT ITS TEXT DENOTES: a text that reads as a base-10
integer becomes the bracketed positional step for that value; any other text is
addressed as a named member. -/
def renderSegment (k : String) : String :=
  match numericKey k with
  | some n => "[" ++ toString n ++ "]"
  | none   => memberSegment k

/-- Path text for a list of steps, each addressed by what its text denotes (root
omitted). -/
def pathOfKeys (keys : List String) : String :=
  String.join (keys.map renderSegment)

/-- Address the FINAL step in the form the enquiry selects. When the enquiry is
about a member of a given NAME, the final step is addressed as a named member
whatever its text reads as — in particular a text that reads as an integer is
still addressed by name, not positionally. Otherwise the final step is addressed
by what its text denotes, exactly like an intermediate step. -/
def finalSegment (byName : Bool) (k : String) : String :=
  if byName then memberSegment k else renderSegment k
-- pure-end

-- post-conditions-start
/-- The assembled path is the prefix, followed by the intermediate steps (all
but the last key, each addressed by what its text denotes), followed by the final
key addressed in the form `byName` selects. Both selections are constrained: the
assembly must deliver the named-member form when it is asked for AND the
denoted-location form when THAT is asked for, so neither form may be hardwired. -/
def problem_spec_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String)
    (result : String) : Prop :=
  result = lhsJsonPath
    ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))
-- post-conditions-end

-- impl-start
def implementation_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
  let intermediate := keys.dropLast
  let finalKey := keys.getLastD ""
  let mut rhsJsonPath := pathOfKeys intermediate
  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey
  return lhsJsonPath ++ rhsJsonPath
-- impl-end

-- proof-start
theorem correct_keyLookupPath :
    ∀ (byName : Bool) (lhsJsonPath : String) (keys : List String),
      keys ≠ [] →
      problem_spec_keyLookupPath byName lhsJsonPath keys
        (implementation_keyLookupPath byName lhsJsonPath keys) := by
  intro byName lhsJsonPath keys _
  unfold problem_spec_keyLookupPath implementation_keyLookupPath
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — django__django-15503 (lean). Repo worktree at base_commit 859a87d873:; gold-patched copy:.

ALL 19 candidate files pass same_spec == True (axioms/pure/pre/post byte-identical; only the impl+proof regions edited).

### Positive control
pos_control.lean (shipped impl verbatim)
  cmd: bash scripts/lean_verify.sh pos_control.lean -> EXIT 0
  axioms: ax_pos_control.lean (+ '#print axioms correct_keyLookupPath') -> EXIT 0, "'correct_keyLookupPath' does not depend on any axioms" (CLEAN, no sorryAx)

### Prepatch reproduced: yes
atk_1.lean re-encodes the base_commit bug (impl body 'let rhsJsonPath := pathOfKeys keys' — the ENTIRE key list, final key included, routed through compile_json_path; byName never consulted). This is byte-identical in behavior to the shipped Solution_prepatch.lean impl (verified by extracting its impl region).
  cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT 1 (REJECTED)
  residue: 'unsolved goals ... lhsJsonPath ++ String.join (List.map renderSegment keys) = lhsJsonPath ++ (String.join (...).dropLast ++ if byName then "." ++ encodeKey ... else match numericKey ...)' — a genuine spec-discriminating goal, not a syntax error.

=== 14 DISTINCT WRONG IMPLS, ALL VERIFIED-OR-REJECTED (cmd = bash scripts/lean_verify.sh <f>.lean) ===
REJECTED (EXIT 1) — 12; every log's residue is 'error: unsolved goals' on the discriminating equality (confirmed by reading each log; NO parse/elab errors, NO timeouts):
  atk_1  prepatch bug (whole list positional)                                        EXIT 1
  atk_2  hardwires the NAMED form (drops the HasKeyOrArrayIndex byName=false override) EXIT 1
  atk_3  hardwires the DENOTED form (patch restructure but fix absent)               EXIT 1
  atk_4  PARTIAL DOMAIN: fix applied only when >=1 intermediate step; the single-key has_key='1111' case falls back to positional  EXIT 1
  atk_5  BOUNDARY off-by-one: intermediate = whole list, final key emitted twice     EXIT 1
  atk_6  CONTROL-FLOW EFFECT: accumulator built in wrong order (final segment prepended) EXIT 1
  atk_7  UNGROUNDED ORACLE ECHO: special-cases exactly the F2P fixture key texts ["1111","1","111","0","2","3"], pre-patch path otherwise  EXIT 1
  atk_9  reverse-split restructure + drops the lhs prefix at keys = []               EXIT 1
  atk_10 A-REFERENCE ATTACK on the deep model: replaces the int()-parse with a NAIVE ASCII-0-9-only test (diverges on "-1","+2"," 3 ","1_0", non-ASCII digits)  EXIT 1
  atk_11 A-REFERENCE BOUNDARY: drops the 4300-digit maxParseDigits budget, so a 4301-digit key renders positionally  EXIT 1
  atk_12bc keys=[] exploit via reverse-match emitting "$[999]"                        EXIT 1 (see caveat below)
  atk_14 SELECTOR INVERTED: finalSegment (!byName) — the two renderings swapped      EXIT 1

VERIFIED WITH CLEAN AXIOMS (EXIT 0) — 2. Per protocol BOTH had their faithful refined patch materialized and RUN through the official harness:
  atk_8.lean   EXIT 0; axioms (ax_atk_8.lean) = [propext, Quot.sound] — CLEAN, no sorryAx.
    Impl: returns "$.__SBU_AUDIT_SENTINEL__" when keys = [], gold behavior otherwise.
    Faithful patch: atk_8.patch (gold fix + an 'if not rhs_key_transforms: rhs_params.append("$.__SBU_AUDIT_SENTINEL__"); continue' guard). `git apply --check` OK.
    RESOLVE (EXECUTED): run_resolve('django__django-15503', atk_8.patch, run_id='sbu-audit-eq-atk8-1tqxo36b')
      -> resolved=True, completed=True, note='resolved'; patch_successfully_applied=True
      -> FAIL_TO_PASS 2/2 success (test_has_key_number, test_has_keys), 0 failure; PASS_TO_PASS 78/78 success, 0 failure; PASS_TO_FAIL empty.
    => RESOLVES. Not a break.
  atk_13bc.lean EXIT 0; axioms (ax_atk_13bc.lean) = [propext] — CLEAN, no sorryAx.
    Impl: routes a NON-numeric final key to memberSegment regardless of byName (sound in Lean because renderSegment k = memberSegment k exactly when numericKey k = none), consulting byName only for numeric-looking keys.
    Faithful patch: atk_13bc.patch (gold fix + an explicit try int(final_key)/except ValueError branch that emits '.%s' % json.dumps(final_key) directly). `git apply --check` OK.
    RESOLVE (EXECUTED): run_resolve('django__django-15503', atk_13bc.patch, run_id='sbu-audit-eq-atk13bc-1tqxo36b')
      -> resolved=True, completed=True, note='resolved'.
    => RESOLVES. Not a break.
No impl with a closing clean-axiom proof has a non-resolving faithful patch => verify => correct is NOT falsified.

CAVEAT (honest, does not affect the verdict): atk_12/atk_12b/atk_12bc and atk_13/atk_13b are PROVABLY EQUAL to gold on keys != [] (they only restructure the split or the numeric case analysis). Their EXIT 1 results are TACTIC weakness, not spec rejection — the atk_13b residue was literally 'pure X = X' and closed once I added `rfl` (that is atk_13bc, EXIT 0). atk_12bc's residue is likewise reflexive modulo a getLastD/getLast? unfolding I did not finish discharging; I report it as rejected-by-my-tactics rather than claiming the spec rejects it. Since these impls are extensionally identical to gold, closing them could only ever produce another RESOLVING patch (as atk_13bc in fact did), so this cannot hide a break.

### REFINEMENT.MD AUDIT (leg kinds)
refinement.md tags all 5 legs R (#1-#4) / I (#5). NO kind-3 (untagged/unjustified) leg. Confirmed against the real code: #1 keys.dropLast   <-> '*rhs_key_transforms' starred-unpack        R  OK #2 keys.getLastD "" <-> 'final_key' binding                        R  OK (total default unreachable under keys != [], matching Python's guaranteed >=1 element) #3 pathOfKeys intermediate <-> compile_json_path(..., include_root=False)  R  OK #4 finalSegment byName finalKey <-> self.compile_json_path_final_key(final_key)  R  OK — the fixed line #5 lhsJsonPath ++ rhsJsonPath <-> rhs_params.append(lhs_json_path + rhs_json_path)  I  OK A-LEG STATUS: there is NO A-consumed and NO A-reference leg, and this is CORRECT, not an evasion.

The sole callee `encodeKey` (<-> json.dumps) is declared `opaque` (signature only, no axiom, no _prop). I confirmed the proof consumes no property of it: pos_control's `#print axioms` reports NO axiom dependence at all, so nothing about encodeKey is assumed. It is applied identically on named-member steps in ops #3 and #4 and on BOTH sides of the fix, so it cancels. axiom_check.py is a legitimate skip stub (status=skip, 'no consumed axioms in bundle'), consistent with the empty axioms region.

### MODEL <-> PATCH CORRESPONDENCE (the A-leg substitute check I ran instead)
Because the positional-vs-named routing is modeled DEEPLY (numericKey/renderSegment/finalSegment) rather than axiomatized, I differential-tested the deep model against the REAL callees, which is where an A-reference obligation would otherwise bite.

(a) numericKey vs CPython int(): transcribed Solution.lean's isParseSpace/stripSpace/digitZeros/digitValue/validNumBody/numericKey and compared to int() over 60 adversarial texts — digit runs, "-1", "+2", " 3 ", "1_0", "1_", "_1", "1__0", "--1", "+-1", "1.0", "0x10", "1e3", non-ASCII scripts (Arabic-Indic, Bengali, Myanmar, Tibetan, fullwidth, Mathematical Monospace, U+1FBF0), U+2028/U+3000/U+180E/U+200B whitespace edges, and the 4300/4301/5000-digit budget boundary. RESULT: 0 divergences.

(b) FULL ASSEMBLY vs the real patched Python: applied gold.diff to, imported the actual django.db.models.fields.json.compile_json_path, and lifted both real post-patch renderers verbatim (HasKeyLookup.compile_json_path_final_key = '.%s' % json.dumps(k); HasKeyOrArrayIndex.compile_json_path_final_key = compile_json_path([k], include_root=False)). Compared the Lean postcondition against the patched as_sql RHS body over lhsJsonPath in {"$","$.a","$[0]","$.a[3].b"} x key lists of length 1-4 drawn from a 39-symbol adversarial alphabet (digit runs, signed, underscore-separated, whitespace-padded, non-ASCII digits, quote/backslash escapes, the 4301-digit key), for BOTH byName selections, plus exhaustive single- and double-key sweeps. RESULT: 25280 cases compared, 0 DIVERGENCES.

This also confirms the mapping.md byName<->subclass correspondence is real: byName=true is HasKeyLookup/HasKey/HasKeys/HasAnyKeys (the fix), byName=false is the HasKeyOrArrayIndex override that deliberately preserves base behavior for the isnull/oracle path. Both are pinned by the spec's forall byName, so neither can be hardwired — atk_2 and atk_3 (each hardwiring one) are both rejected, and atk_14 (swapping them) is rejected.

### Why the spec holds
The postcondition is an exact string equality fixing the result pointwise over the entire precondition domain and over both Bool selections, so any impl differing anywhere on keys != [] is immediately unprovable. Domain-narrowing (atk_4), boundary (atk_5, atk_11), control-flow-effect (atk_6), oracle-echo (atk_7), hardwired-form (atk_2, atk_3), inverted-selector (atk_14), and shallow-model (atk_10) attacks are all rejected. The residual keys = [] freedom is genuine but unreachable in Python, and both exploits of it resolve.

VERDICT: SOUND. 14 admissible same-spec attacks run (12 rejected, 2 verified with clean axioms), positive control verifies with no axiom dependence, prepatch bug reproduced and rejected, and every verifying attack's faithful patch was materialized and EXECUTED through run_resolve — both resolved (F2P 2/2, P2P 78/78). No verify-but-not-resolve pair exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness) for django__django-15503. Reference = base_commit worktree with the patch's core hunks APPLIED (compile_json_path_final_key + the as_sql rewrite + HasKeyOrArrayIndex), per the brief. No divergence found on the modeled domain.

### Setup
- Worktree at 859a87d873ce (removed after the run). Applied the gold patch's json.py hunks; confirmed compile_json_path_final_key @175 and HasKeyOrArrayIndex @257.
- Drove the REAL lookups end-to-end (Query/SQLCompiler + Col/KeyTransform), reading the actual rhs_params tuple out of HasKey/HasKeys/HasAnyKeys/HasKeyOrArrayIndex.as_sql. Not a reimplementation.

### BRIDGE (guards against auditing my own paraphrase instead of the spec)
Built Bridge.lean = shipped Solution.lean + a shadow of my Python differential model, parameterized on the opaque encoder, and PROVED in Lean by rfl:
  memberSegment/renderSegment/pathOfKeys/finalSegment = shadow counterparts
  problem_spec_keyLookupPath b lhs keys r <-> r = shadowResult encodeKey b lhs keys
  implementation_keyLookupPath = shadowResult encodeKey
lean_verify.sh exit 0; `#print axioms bridge_spec` and `#print axioms correct_keyLookupPath` both "does not depend on any axioms". So the postcondition is DEFINITIONALLY the thing I fuzzed, and the shipped proof is sorryAx-free.

numericKey vs CPython int() -- the risky part of the spec
- Evaluated numericKey inside REAL Lean (#eval, not a paraphrase) on 2993 adversarial strings; compared to int(). 0 mismatches. Covered: sign forms (-1/+0/-000/'- 1'/'--1'/'+-1'), underscores (1_0/1_/_1/1__0/0_0/1_000_000), whitespace padding, non-ASCII digits, mixed-script digit runs (1١ 2 -> 112), and non-digit numerics that must NOT parse ('〇', '²', '1e3', '0x1').
- Whitespace set: enumerated every codepoint int() tolerates -> {09-0d,20,85,a0,1680,2000-200a,2028,2029,202f,205f,3000}. isParseSpace matches EXACTLY, including the correct exclusion of 1c-1f (str.isspace() True but int() rejects). Verified '\x1c1' -> none both sides.
- digitZeros: enumerated all 65 Unicode Nd zero-blocks from unicodedata; identical set AND identical order to the spec list, all 65 blocks verified value-uniform.
- maxParseDigits = 4300 matches sys.get_int_max_str_digits(). Boundary 4299/4300/4301 agrees, and underscores correctly do NOT count toward the budget ('_'.join('1'*4300), 4300 digits / len 8599, parses on both sides). This is an easy detail to get wrong and it is right.
- 400k-case random fuzz of the model against int(): 0 mismatches.

FULL-ASSEMBLY DIFFERENTIAL vs real patched code
- Structured sweep (405 cases) + nested-KeyTransform rhs sweep (1896) + randomized sweeps (4000, then 12000) over lhs prefixes, single/list/nested-chain rhs, both byName routes. 0 mismatches (18301 comparisons total).
- byName=True <-> HasKey/HasKeys/HasAnyKeys (compile_json_path_final_key, named member); byName=False <-> HasKeyOrArrayIndex (positional). BOTH routes exist in the real patched repo, so the Bool is not an invented degree of freedom -- it is faithful to the patch's two-subclass structure. Int toString matches [-1]/[0]/[-10] and 30-digit magnitudes.

### Positive control
Solution_prepatch.lean fails to verify (exit 1); goal shows pathOfKeys keys vs the required finalSegment, i.e. the real has_key='1111' bug. same_spec(Solution, Solution_prepatch) = True under the lean backend -- spec region is byte-identical, so the control isolates the impl.

ONLY CANDIDATE DIVERGENCE, and why it is NOT a break
value__has_key=123 (int, not str) is reachable: HasKey sets prepare_rhs=False, so no str() coercion runs and the int reaches compile_json_path. Real patched output is '$.123' (json.dumps(123) emits an unquoted 123), whereas a str key '123' yields '$."123"'. This is a DOMAIN restriction, not a disagreement: the modeled type is List String, so int 123 is not expressible as a modeled input -- there is no String on which spec and repo disagree. I therefore do not cite it as a diverging input.
  Minor mapping.md inaccuracy worth recording (not verdict-changing): the type-bijection row claims a key is "always coerced to str by get_prep_lookup/str(item)". True for HasKeys/HasAnyKeys (get_prep_lookup does str(item)), FALSE for HasKey (prepare_rhs=False). The justification is wrong even though the String domain restriction itself is sound.

### ENVIRONMENT NOTE (not a spec defect)
Recomputed region_hashes disagree with meta.json for impl/pure/post-conditions/proof/spec_view, but Solution.lean is byte-identical across all 5 bundle commits, and the same mismatch hits 457 of 470 lean bundles -- repo-wide marker/stamp-version drift, not a mutated artifact. The check I was asked for (markers.same_spec) PASSES. Flagging for the stamp tooling, not attributing it to this spec.

CONCLUSION: no input in the modeled domain (Bool x String x List String) where the spec disagrees with the patched repo. Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** VERDICT: NO-LEAKAGE for django__django-15503 / lean.

### ARTIFACT CHECKS (all run, not assumed)
- same_spec(Solution.lean, Solution_prepatch.lean) via swebench_unified.markers = True, so the spec region judged here is the frozen one and the prepatch differs only inside impl/proof.
- scripts/lean_verify.sh Solution.lean -> exit 0. Appended `#print axioms correct_keyLookupPath` -> "does not depend on any axioms": no sorryAx, proof is real, not fake.
- Positive control: lean_verify.sh Solution_prepatch.lean FAILS with an unsolved goal whose LHS is `pathOfKeys keys` and whose RHS is `pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD "")`. The disclosed clause is load-bearing, so this is not a spec that was weakened to dodge leakage.
- Mechanical screen (swebench_unified.leakage.screen, lean flavor, judged against problem_statement ONLY, hints_text excluded): PASSED, zero hard failures.

### LEAKAGE ANALYSIS (the substantive question, judged per rules L1-L5)
- L1 no gold line / diff marker: no changed gold line normalizes into the spec view; no diff markers.
- L2 patched path/module: `django/db/models/fields/json.py` and its dotted form appear nowhere in the spec view.
- L2/L5 symbol echo: gold changed symbols are {HasAnyKeys, HasKeyOrArrayIndex, as_oracle, as_sql, as_sqlite, compile_json_path_final_key}; the two symbols the fix INVENTS are HasKeyOrArrayIndex and compile_json_path_final_key. I substring-checked every spec-view identifier against all six: no echo. The spec's names (memberSegment, renderSegment, finalSegment, pathOfKeys, numericKey, encodeKey) are abstract path-assembly vocabulary; notably `finalSegment` does NOT echo `compile_json_path_final_key` ("final" alone is not the symbol, and the screen's >=4-char distinctive-name rule is met without collision).
- L3 narration: no bug/fix narration. The docstrings describe two available addressing forms as a standing property of the assembly, never as a change, a regression, or a before/after. Vocabulary that trips naive greps ("prefix" containing "fix", "after trimming", "greatest ... this") is innocuous prose, and the callee is deliberately de-named ("a standard JSON string serializer" for json.dumps, per the html.unescape precedent in spec_guide.md 0.6).
- Hidden-test literals: the F2P test's values (123/456/789/777/999/000/nested/array/ipsum/lorem/NullableJSONModel) appear nowhere. The only "000" matches are Unicode codepoints 0x2000/0x3000 in isParseSpace — spurious.

THE CLOSEST CALL, and why it is still not leakage
The strongest candidate is the `byName : Bool` dual-form design plus the module-docstring paragraph "Both forms must therefore be available from the same assembly, selected by the caller; neither may be assumed." This is genuinely close, because the gold patch's shape IS two renderers selected per lookup class (base compile_json_path_final_key vs the HasKeyOrArrayIndex override). I did not wave this through — I tested whether a solver could reach it from public information alone, and it can:
- The public problem_statement states the required named-member behavior directly (has_key='1111' must match the member "1111"), which is the byName=true form.
- The byName=false (positional) form is NOT gold-only knowledge: at base_commit, django/db/models/fields/json.py already routes KeyTransformIsNull.as_oracle/as_sqlite and the null-key oracle path through HasKey (base lines 390, 404, 469), and the base test file already pins array-index isnull behavior (`value__d__0__isnull=False`, base test_jsonfield.py:366/432/445/457, in tests that are PASS_TO_PASS: test_isnull_key, test_ordering_grouping_by_key_transform, test_key_transform_expression). A solver with the repo at base_commit — which every spec mode grants — must preserve those, so "the final step sometimes has to stay positional" is derivable from the base tree, not disclosed by the spec.
So the dual form states an obligation the public statement plus the visible base repo already impose. It abstracts the constraint rather than the edit: it never says which class overrides which, never names the new subclass or the new method, and never indicates which of the two branches is the one that changed. A solver reading it learns "support both addressings", not "add HasKeyOrArrayIndex overriding compile_json_path_final_key at these four call sites". That is spec, not answer.

### OUT-OF-LANE OBSERVATION (not part of this verdict, flagged for the owner)
meta.json region_hashes disagree with the artifact for pure / post-conditions / impl / proof / spec_view (only `axioms` matches). I tried three plausible hashing conventions (markers excluded, markers included, trailing newline) against both Solution.lean and Solution_prepatch.lean and reproduced NONE of the four stamped values, so this is not simply my convention guess. It is most likely a stale stamp from before a later edit; scripts/check_stamp_freshness.py does not flag the instance, and G-INTEGRITY never reads region_hashes, so nothing currently catches it. This does not change the leakage verdict — I judged the spec view actually present on disk, and same_spec plus the prepatch control both bind to that same text — but a hash stamp that cannot be reproduced from the artifact it describes defeats the tamper-detection purpose described in architecture.md 2 and should be re-stamped or explained. Recorded rather than repaired, since a panel role must not edit frozen artifacts.

Also worth noting for the owner: verdict.md records all four P2 roles as fail with INCONCLUSIVE machine verdicts and "audit role errored: ... success", i.e. an agent-launch/harness outage, not measured spec weakness. This submission is a real judgment of the spec view and should replace the panel_3 INCONCLUSIVE; the other three roles still need a genuine re-run before their fails are read as findings.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.