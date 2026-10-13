# P2 adversarial audit — astropy__astropy-8707

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,12 +81,12 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- PREPATCH BUG: a raw octet source is NOT accepted -- it is refused
+    -- instead of being decoded byte-for-byte.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  _ => Except.error ImageErr.rawNotAccepted
     return image
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,10 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
-    let image : Except ImageErr (List Char) :=
-      match src with
-      | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
-    return image
+    -- UNGROUNDED ORACLE ECHO: hand back the specification function itself;
+    -- the impl performs no independent computation whatsoever.
+    return imageSpec src
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,19 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- PARTIAL DOMAIN: decode only when every octet is in range; otherwise
+    -- refuse the source. The `require` hides the refusing branch.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          if (∀ x ∈ b, x < 256) then Except.ok (codepointsOf b)
+          else Except.error ImageErr.rawNotAccepted
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp only [imageSpec, if_pos require_1]
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,27 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- PARTIAL DOMAIN 2: reduce every octet mod 256 before decoding. The
+    -- `require` makes the reduction a no-op on admissible inputs.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b => Except.ok (codepointsOf (b.map (fun x => x % 256)))
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  have key : ∀ (l : List Nat), (∀ x ∈ l, x < 256) →
+      codepointsOf (l.map (fun x => x % 256)) = codepointsOf l := by
+    intro l
+    induction l with
+    | nil => intro _; simp [codepointsOf]
+    | cons x xs ih =>
+        intro h
+        have hx : x < 256 := h x (by simp)
+        simp only [List.map_cons, codepointsOf_cons, Nat.mod_eq_of_lt hx]
+        rw [ih (fun y hy => h y (by simp [hy]))]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp only [imageSpec, key b require_1]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,18 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- BOUNDARY / WRONG CODEC: octets >= 128 are folded into the 7-bit range
+    -- (a plausible "FITS is ASCII" reading). NOT byte-for-byte.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          Except.ok (codepointsOf (b.map (fun x => if x < 128 then x else x - 128)))
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,16 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- BOUNDARY / OFF-BY-ONE: the last octet of the raw source is dropped.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b => Except.ok (codepointsOf b.dropLast)
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,22 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- BOUNDARY: the EMPTY raw source is special-cased into a refusal. The
+    -- precondition does not exclude the empty octet sequence.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          match b with
+          | []      => Except.error ImageErr.rawNotAccepted
+          | _ :: _  => Except.ok (codepointsOf b)
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => cases b with
+    | nil => simp [imageSpec, codepointsOf]
+    | cons x xs => simp [imageSpec]
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,31 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- CONTROL-FLOW RESHAPE: accumulate left-to-right with foldl and reverse
+    -- at the end, rather than the front-recursive codepointsOf.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          Except.ok ((b.foldl (fun acc x => Char.ofNat x :: acc) []).reverse)
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  have gen : ∀ (l : List Nat) (acc : List Char),
+      l.foldl (fun a x => Char.ofNat x :: a) acc
+        = (codepointsOf l).reverse ++ acc := by
+    intro l
+    induction l with
+    | nil => intro acc; simp [codepointsOf]
+    | cons x xs ih =>
+        intro acc
+        simp only [List.foldl_cons, ih, codepointsOf_cons, List.reverse_cons,
+                   List.append_assoc, List.cons_append, List.nil_append]
+  have key : ∀ (l : List Nat),
+      (l.foldl (fun acc x => Char.ofNat x :: acc) []).reverse = codepointsOf l := by
+    intro l; rw [gen l []]; simp
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp only [imageSpec, key b]
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,20 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- CONTROL-FLOW EFFECT / UNBOUNDED-INPUT BOUNDARY: only sources up to one
+    -- record width are decoded; anything longer is refused. Nothing in the
+    -- precondition bounds the octet-sequence length.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          if b.length ≤ 80 then Except.ok (codepointsOf b)
+          else Except.error ImageErr.rawNotAccepted
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,18 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- WRONG BRANCH: the CHARACTER source is pushed through the octet decoder
+    -- as well (re-interpreting characters as octet values), instead of being
+    -- used as-is.
     let image : Except ImageErr (List Char) :=
       match src with
-      | Source.text s => Except.ok s
+      | Source.text s => Except.ok (codepointsOf (s.map Char.toNat))
       | Source.raw  b => Except.ok (codepointsOf b)
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,16 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- ORDER: the decoded character image comes back reversed.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b => Except.ok (codepointsOf b).reverse
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,29 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- CONTROL-FLOW RESHAPE 2: dispatch on emptiness first, then decode.
+    -- Same extensional function, restructured control flow.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          if b.isEmpty then Except.ok []
+          else Except.ok (b.foldr (fun x acc => Char.ofNat x :: acc) [])
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  have key : ∀ (l : List Nat),
+      l.foldr (fun x acc => Char.ofNat x :: acc) [] = codepointsOf l := by
+    intro l
+    induction l with
+    | nil => simp [codepointsOf]
+    | cons x xs ih => simp [codepointsOf, ih]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b =>
+      cases b with
+      | nil => simp [imageSpec, codepointsOf]
+      | cons x xs => simp only [imageSpec, List.isEmpty_cons, if_neg, key]
+                     simp [key]
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,20 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- _pad PROBE: the impl performs the fixed-width normalization itself,
+    -- inside the modeled function, rather than leaving it to the unchanged
+    -- downstream normalizer.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          let img := codepointsOf b
+          Except.ok (img ++ List.replicate (80 - img.length) ' ')
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,17 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- R-LEG PROBE: round-trip the decoded image through the String carrier
+    -- (mapping.md section 2's str <-> List Char bijection) before returning it.
     let image : Except ImageErr (List Char) :=
       match src with
-      | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.text s => Except.ok (String.mk s).toList
+      | Source.raw  b => Except.ok (String.mk (codepointsOf b)).toList
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,15 +81,25 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
-    let image : Except ImageErr (List Char) :=
-      match src with
-      | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
-    return image
+    -- CONTROL-FLOW EFFECT: consume the octet sequence with an imperative
+    -- while-loop, appending each code-point character to an accumulator,
+    -- rather than the front-recursive codepointsOf.
+    match src with
+    | Source.text s => return Except.ok s
+    | Source.raw  b =>
+        let mut rest := b
+        let mut acc : List Char := []
+        while !rest.isEmpty
+        invariant acc ++ codepointsOf rest = codepointsOf b
+        decreasing rest.length
+        do
+          match rest with
+          | []      => rest := []
+          | x :: xs =>
+              acc := acc ++ [Char.ofNat x]
+              rest := xs
+        return Except.ok acc
     -- impl-end
 
 prove_correct buildImage by
-  loom_solve
-  simp [imageSpec]
+  loom_solve <;> simp_all [imageSpec, codepointsOf]
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,19 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- BOUNDARY at the octet-range EDGE: the top octet 255 is mapped to a
+    -- replacement character instead of its own code point. Every other octet
+    -- is byte-for-byte correct, so only the range boundary diverges.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          Except.ok (codepointsOf (b.map (fun x => if x = 255 then 63 else x)))
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,17 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- BOUNDARY at the other edge: NUL octets are dropped from the image
+    -- (a plausible C-string reading of a raw octet source).
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b => Except.ok (codepointsOf (b.filter (fun x => x != 0)))
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,21 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- PARTIAL DOMAIN 3 / VACUITY: the decode is guarded by a condition that
+    -- is FALSE on the entire admissible domain (`require` forces every octet
+    -- < 256), so on every real input this arm REFUSES the source -- the
+    -- prepatch behavior wearing a guard.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          if (∃ x ∈ b, 256 ≤ x) then Except.ok (codepointsOf b)
+          else Except.error ImageErr.rawNotAccepted
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,19 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- _pad-COLLISION PROBE: append a trailing space to the decoded image.
+    -- The downstream fixed-width normalizer ABSORBS trailing spaces
+    -- (_pad "X" == _pad "X "), so this is unobservable after normalization --
+    -- it verifies only if the spec fails to pin the image PRE-normalization.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b => Except.ok (codepointsOf b ++ [' '])
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,15 +81,21 @@
   ensures out = imageSpec src
   do
     -- impl-start
-    -- A raw octet source is decoded to a character image (each octet → the
-    -- character with that code-point value); a character source is used as-is.
+    -- CODEC SUBSTITUTION: octets below 128 decode byte-for-byte; high octets
+    -- are REFUSED, exactly as a 7-bit codec would. Agrees with the intended
+    -- behavior on every ASCII source, diverges on the 128 high octets that
+    -- the byte-for-byte claim covers.
     let image : Except ImageErr (List Char) :=
       match src with
       | Source.text s => Except.ok s
-      | Source.raw  b => Except.ok (codepointsOf b)
+      | Source.raw  b =>
+          if (∀ x ∈ b, x < 128) then Except.ok (codepointsOf b)
+          else Except.error ImageErr.rawNotAccepted
     return image
     -- impl-end
 
 prove_correct buildImage by
   loom_solve
-  simp [imageSpec]
+  cases src with
+  | text s => simp [imageSpec]
+  | raw b => simp [imageSpec]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The changed operation — normalizing a construction source
   to its character image, accepting a raw octet source as readily as a
   character source — is modeled DEEPLY in the `pure` region (`imageSpec`,
   `codepointsOf`). The fixed-width normalizer that runs AFTERWARD on the
   resulting image is an unchanged downstream helper, applied identically in
   both source cases; it is orthogonal to the behavior under spec and is not
   part of the model (refinement.md step C, mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- A construction source is EITHER a character image already in hand, OR a raw
   octet sequence (each element an octet value, 0–255). The desired behavior is
   that BOTH are acceptable inputs. -/
inductive Source where
  | text (s : List Char)
  | raw  (b : List Nat)
  deriving DecidableEq

/- The single way construction can be refused: a raw octet sequence is rejected
   instead of being accepted as a valid source. This is the only outcome the
   desired behavior distinguishes from success. -/
inductive ImageErr where
  | rawNotAccepted
  deriving DecidableEq

/- The character image obtained from a raw octet sequence: each octet is mapped
   to the character whose code point equals that octet's value (so every octet
   in 0–255 yields exactly one character, byte-for-byte, with no re-encoding).
   Front-recursive so a single unfold is available per element (the Velvet fold
   pattern); the deep model G-AX validates against the real octet→character
   interpretation (mapping.md §3.1, A-reference). -/
def codepointsOf : List Nat → List Char
  | []      => []
  | b :: bs => Char.ofNat b :: codepointsOf bs

@[grind] lemma codepointsOf_nil : codepointsOf [] = [] := rfl
@[grind] lemma codepointsOf_cons (b : Nat) (bs : List Nat) :
    codepointsOf (b :: bs) = Char.ofNat b :: codepointsOf bs := rfl

/- The intended character image obtained from a construction source, before the
   unchanged downstream fixed-width normalizer runs, as
   `Except ImageErr (List Char)` (`error` = the source was refused, `ok img` =
   the character image to normalize and store):

     * a character source is accepted and its image is the source itself;
     * a raw octet source is ALSO accepted — its image is the per-octet
       code-point interpretation above.

   No source is ever refused; a raw octet source is treated exactly like a
   character source whose characters are the per-octet code points. -/
def imageSpec (src : Source) : Except ImageErr (List Char) :=
  match src with
  | Source.text s => Except.ok s
  | Source.raw  b => Except.ok (codepointsOf b)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the character image from a construction source (the image the unchanged
   downstream fixed-width normalizer is then applied to, identically in either
   case). Desired behavior: a raw octet source must NOT be refused — it is
   accepted exactly as a character source is, by interpreting each octet (0–255)
   as the character with that code point. -/
method buildImage (src : Source) return (out : Except ImageErr (List Char))
  require (match src with
            | Source.raw b => ∀ x ∈ b, x < 256
            | Source.text _ => True)
  ensures out = imageSpec src
  do
    -- impl-start
    -- A raw octet source is decoded to a character image (each octet → the
    -- character with that code-point value); a character source is used as-is.
    let image : Except ImageErr (List Char) :=
      match src with
      | Source.text s => Except.ok s
      | Source.raw  b => Except.ok (codepointsOf b)
    return image
    -- impl-end

prove_correct buildImage by
  loom_solve
  simp [imageSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) — astropy__astropy-8707 velvet. Verdict: SOUND.
Scratch dir: (fresh; worktree ./wt at base_commit a85a0747c5).
NOTE ON `patches`: each entry holds the card.py hunk inline plus a pointer to the full on-disk .patch file that was ACTUALLY fed to run_resolve (the full texts include the gold-verbatim header.py site B and total ~37KB).

PROTOCOL EXECUTED. 20 same-spec attacks + positive control + gold control + a site-A-only probe.
All 21 Lean files: markers.same_spec(frozen, attack, velvet.language) == True AND
variant_scope.unsound_evasions == [] (admissible: no new axiom/sorry/native_decide, prove_correct
header retained). Every verification: `bash scripts/lean_verify.sh <file>`, run as
concurrent background batches of 4. Positive control = byte-identical frozen Solution.lean -> EXIT 0.

### VERIFY RESULTS (exit 0 = verifies, 1 = rejected)
 verifies (7): atk_2, atk_3, atk_4, atk_8, atk_12, atk_14, atk_15
 rejected (13): atk_1 atk_5 atk_6 atk_7 atk_9 atk_10 atk_11 atk_13 atk_16 atk_17 atk_18 atk_19 atk_20
All 13 rejections are genuine `error: unsolved goals` on case
«ensures_1: out = imageSpec src».raw — the spec's own obligation, not tactic mishaps. Spot-checked
residual goals: atk_19 leaves `|- False`, atk_20 leaves `|- forall x in b, x < 128` under
`require_1 : forall x in b, x < 256` — i.e. exactly the semantic divergence, unprovable.

EVERY VERIFYING ATTACK'S FAITHFUL REFINED PATCH WAS MATERIALIZED AND RUN THROUGH run_resolve (command: `python resolve_one.py <name>`, which calls swebench_unified.harness.run_resolve('astropy__astropy-8707', patch, run_id='geq8707k-<name>'); per-attack JSON in <name>.resolve.json). Refinement used mapping.md §2's bijection (str<->Source.text/List Char, bytes<->Source.raw/List Nat, chr<->Char.ofNat, bytes.decode('latin-1')<->codepointsOf), with site B (header.py) kept GOLD-VERBATIM per refinement.md §B.

OBSERVED RESULTS — all seven RESOLVED, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 11/11 pass: atk_2.patch (oracle echo -> the decode itself)               RESOLVED atk_3.patch (partial-domain guard + else-raise)              RESOLVED atk_4.patch (octets reduced mod 256 first)                   RESOLVED atk_8.patch (foldl-onto-front then reverse)                  RESOLVED atk_12.patch (emptiness dispatch then foldr)                 RESOLVED atk_14.patch (String-carrier round-trip)                     RESOLVED atk_15.patch (imperative while-loop + decreasing measure)    RESOLVED Controls: gold.patch RESOLVED (harness lane healthy); atk_siteA_only.patch (gold card.py hunk ONLY, header.py left at base_commit) RESOLVED — this MECHANIZES refinement.md §B's ungraded-site claim. => No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds.

### ATTACK CLASSES COVERED (all required classes present)
 prepatch bug          atk_1  raw source REFUSED (Except.error rawNotAccepted) -> REJECTED
 ungrounded oracle echo atk_2  `return imageSpec src`, computes nothing -> verifies, patch RESOLVES
 partial domain        atk_3 (guard+refuse), atk_4 (mod 256), atk_18 (guard FALSE on the whole
                       admissible domain = prepatch wearing a guard -> REJECTED), atk_20 (7-bit codec)
 boundary              atk_5 (high octets folded -128), atk_6 (dropLast), atk_7 (empty raw refused),
                       atk_9 (length>80 refused), atk_11 (reversed), atk_16 (octet 255 -> '?'),
                       atk_17 (NUL dropped), atk_19 (trailing space appended) — ALL REJECTED
 control-flow effect   atk_8 (foldl+reverse), atk_12 (emptiness dispatch+foldr),
                       atk_15 (real `while` loop, invariant + `decreasing rest.length`) -> all verify,
                       all patches RESOLVE (correct reshapes, as they should)
 wrong branch          atk_10 text source pushed through the octet decoder -> REJECTED
 omitted-callee probe  atk_13 impl performs the fixed-width padding ITSELF -> REJECTED
 R-leg probe           atk_14 String-carrier round-trip -> verifies, patch RESOLVES

### TWO ATTACKS WORTH SINGLING OUT (the sharpest available, both REJECTED)
 atk_20 CODEC SUBSTITUTION: decodes octets <128 byte-for-byte and REFUSES high octets, exactly as an
 `ascii` codec would. It agrees with the gold patch on the FAIL_TO_PASS witness b"ABC     = 'abc'"
 (pure ASCII) and on all 11 PASS_TO_PASS — so the TEST SUITE CANNOT TELL IT APART from correct. The
 spec rejects it anyway (residual goal `forall x in b, x < 128`). This is the case where the spec is
 STRICTLY STRONGER than the graded oracle, which is the safe direction and the whole point of the
 bundle. Measured: ascii and utf-8 each reject 128/256 octets, so neither is the modeled map.
 atk_19 _pad-COLLISION: my A4 audit found the real _pad is NOT injective — it absorbs trailing spaces
 (_pad('X') == _pad('X ')), 5 collisions between distinct images in 50k samples. So appending a
 trailing space to the decoded image is UNOBSERVABLE after the omitted downstream normalizer. If the
 spec had been stated only up to the post-_pad image, this would verify. It is REJECTED (`|- False`),
 proving the model pins the image PRE-normalization exactly, as refinement.md A4 claims.

### A-LEG AUDIT (my assigned focus; R/I legs are G-CONF's)
A3 codepointsOf <-> bytes.decode('latin-1') (A-REFERENCE, the only deep model). Lean side (ax_check.lean, via lean_verify.sh): (List.range 256).all (fun b => (Char.ofNat b).toNat == b) evaluates `true`, and (codepointsOf (List.range 256)).map Char.toNat == List.range 256 evaluates `true` — Char.ofNat is the identity on code points across the whole 0-255 block and codepointsOf preserves every octet's value in order.

Python side (ax_py.py): re-derived the reference independently — 0 divergences over all 256 single octets, 8 boundary sequences (empty, all-256-in-order, NUL runs, 0xFF runs, UTF-8 byte pairs, the F2P witness), and 20 000 fuzz sequences seeded 8707 (the bundle's pinned seed). latin-1 confirmed total and single-char on all 256 octets, so mapping.md §3.1's "round-trips ALL 256 octet values" claim holds. The A-reference correspondence to the real callee HOLDS. A4 _pad (I-tagged, NOT axiomatized). pad_check.py transliterates the real _pad verbatim from card.py:1268: 0 branch-identity divergences over 200 000 inputs — _pad is a function of the image alone, blind to which branch produced it, so it genuinely cancels out.

Its non-injectivity is the one hazard and atk_19/atk_13 close it from both sides (spec pins the image tighter than _pad can observe = safe direction). Left as the real repo callee, never axiomatized: no dead axiom ships. A-CONSUMED legs: NONE EXIST. grep for `^\s*axiom` in Solution.lean returns nothing, matching the axioms region's self-declaration. So no A-consumed leg can be over-claimed or dead. A1/A2/A5: A1 (isinstance dispatch <-> match on constructor tag) and A2 (text image used as-is) are R/I and hold under the §2 bijection. A5 — the `error` constructor exists only to express the prepatch refusal — is confirmed by atk_1 failing precisely on the raw arm.

PRECONDITION SCOPE (pre_check.py): `require forall x in b, x < 256` is EXACTLY the Python `bytes` type invariant — 0/100 004 real bytes inputs violate it (incl. bytes(range(256)), 1000-byte 0xFF and NUL runs). It excludes NO reachable input, so it grants no partial-domain escape; the text branch is unconditioned (True). atk_18 confirms the vacuity direction is closed. NO KIND-3: every leg is R, A-reference, or I. The one genuinely changed op — accept a raw octet source by decoding it byte-for-byte — sits DEEPLY in the pure region (imageSpec/codepointsOf), not behind an axiom about the function under change. refinement.md §C's claim is accurate.

CROSS-BACKEND NOTE (flagged, NOT transferred). The NAGINI bundle for this same instance is recorded
G-EQ BROKEN: its atk_2 skipped the decode entirely and still verified, because its `reinterpret` was
axiomatized as the IDENTITY (Ensures(Result() == x)), leaving the boolean literal passed to
pad_runtime as the spec's only trace of "was it decoded?". That hole DOES NOT EXIST HERE: velvet
models the decode DEEPLY as codepointsOf (a computed List Char), not as an identity-axiomatized
callee, so `out = imageSpec src` forces the raw arm to produce the per-octet code-point image. I
re-encoded that exact shape as atk_1 (refuse) and atk_18 (guard-false = decode never runs) and both
are REJECTED with residual goals on the raw arm. I did not carry the nagini verdict over — the
mechanism is backend-specific and re-judging it from this lane would invent a finding.

PRIOR PASSES. meta.json records G-EQ INCONCLUSIVE ("only 0 attacks") and G-PANEL-3 quotes an earlier
"atk_5.lean verifies but its patch does not resolve". Neither is reproducible from retained evidence:
the referenced dir is reaped, and the two surviving
velvet G-EQ scratch dirs (mfsbdk_d, ds2drjlj) show every verifying velvet attack RESOLVING
(5/5 and 3/3). ds2drjlj's non-resolving atk_1/atk_5/atk_6 are NAGINI .py attacks, not velvet, and one
of them (atk_6) failed a PASS_TO_PASS test — consistent with the nagini finding above, not this
bundle. I re-derived everything from scratch rather than inheriting any label.

VERDICT: SOUND. 20 admissible same-spec attacks run; positive control verifies; prepatch bug
reproduced and rejected; all 7 verifying impls' faithful patches EXECUTED through the official
harness and all 7 RESOLVED. No verify-but-not-correct witness exists. The A-legs' correspondence to
the real callees holds under independent re-derivation, and refinement.md contains no kind-3 leg.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_13.lean`, `atk_16.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The changed operation — normalizing a construction source
   to its character image, accepting a raw octet source as readily as a
   character source — is modeled DEEPLY in the `pure` region (`imageSpec`,
   `codepointsOf`). The fixed-width normalizer that runs AFTERWARD on the
   resulting image is an unchanged downstream helper, applied identically in
   both source cases; it is orthogonal to the behavior under spec and is not
   part of the model (refinement.md step C, mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- A construction source is EITHER a character image already in hand, OR a raw
   octet sequence (each element an octet value, 0–255). The desired behavior is
   that BOTH are acceptable inputs. -/
inductive Source where
  | text (s : List Char)
  | raw  (b : List Nat)
  deriving DecidableEq

/- The single way construction can be refused: a raw octet sequence is rejected
   instead of being accepted as a valid source. This is the only outcome the
   desired behavior distinguishes from success. -/
inductive ImageErr where
  | rawNotAccepted
  deriving DecidableEq

/- The character image obtained from a raw octet sequence: each octet is mapped
   to the character whose code point equals that octet's value (so every octet
   in 0–255 yields exactly one character, byte-for-byte, with no re-encoding).
   Front-recursive so a single unfold is available per element (the Velvet fold
   pattern); the deep model G-AX validates against the real octet→character
   interpretation (mapping.md §3.1, A-reference). -/
def codepointsOf : List Nat → List Char
  | []      => []
  | b :: bs => Char.ofNat b :: codepointsOf bs

@[grind] lemma codepointsOf_nil : codepointsOf [] = [] := rfl
@[grind] lemma codepointsOf_cons (b : Nat) (bs : List Nat) :
    codepointsOf (b :: bs) = Char.ofNat b :: codepointsOf bs := rfl

/- The intended character image obtained from a construction source, before the
   unchanged downstream fixed-width normalizer runs, as
   `Except ImageErr (List Char)` (`error` = the source was refused, `ok img` =
   the character image to normalize and store):

     * a character source is accepted and its image is the source itself;
     * a raw octet source is ALSO accepted — its image is the per-octet
       code-point interpretation above.

   No source is ever refused; a raw octet source is treated exactly like a
   character source whose characters are the per-octet code points. -/
def imageSpec (src : Source) : Except ImageErr (List Char) :=
  match src with
  | Source.text s => Except.ok s
  | Source.raw  b => Except.ok (codepointsOf b)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the character image from a construction source (the image the unchanged
   downstream fixed-width normalizer is then applied to, identically in either
   case). Desired behavior: a raw octet source must NOT be refused — it is
   accepted exactly as a character source is, by interpreting each octet (0–255)
   as the character with that code point. -/
method buildImage (src : Source) return (out : Except ImageErr (List Char))
  require (match src with
            | Source.raw b => ∀ x ∈ b, x < 256
            | Source.text _ => True)
  ensures out = imageSpec src
  do
    -- impl-start
    -- A raw octet source is decoded to a character image (each octet → the
    -- character with that code-point value); a character source is used as-is.
    let image : Except ImageErr (List Char) :=
      match src with
      | Source.text s => Except.ok s
      | Source.raw  b => Except.ok (codepointsOf b)
    return image
    -- impl-end

prove_correct buildImage by
  loom_solve
  simp [imageSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) — astropy__astropy-8707 velvet. Verdict: SOUND.
Scratch dir: (fresh; worktree ./wt at base_commit a85a0747c5).
NOTE ON `patches`: each entry holds the card.py hunk inline plus a pointer to the full on-disk .patch file that was ACTUALLY fed to run_resolve (the full texts include the gold-verbatim header.py site B and total ~37KB).

PROTOCOL EXECUTED. 20 same-spec attacks + positive control + gold control + a site-A-only probe.
All 21 Lean files: markers.same_spec(frozen, attack, velvet.language) == True AND
variant_scope.unsound_evasions == [] (admissible: no new axiom/sorry/native_decide, prove_correct
header retained). Every verification: `bash scripts/lean_verify.sh <file>`, run as
concurrent background batches of 4. Positive control = byte-identical frozen Solution.lean -> EXIT 0.

### VERIFY RESULTS (exit 0 = verifies, 1 = rejected)
 verifies (7): atk_2, atk_3, atk_4, atk_8, atk_12, atk_14, atk_15
 rejected (13): atk_1 atk_5 atk_6 atk_7 atk_9 atk_10 atk_11 atk_13 atk_16 atk_17 atk_18 atk_19 atk_20
All 13 rejections are genuine `error: unsolved goals` on case
«ensures_1: out = imageSpec src».raw — the spec's own obligation, not tactic mishaps. Spot-checked
residual goals: atk_19 leaves `|- False`, atk_20 leaves `|- forall x in b, x < 128` under
`require_1 : forall x in b, x < 256` — i.e. exactly the semantic divergence, unprovable.

EVERY VERIFYING ATTACK'S FAITHFUL REFINED PATCH WAS MATERIALIZED AND RUN THROUGH run_resolve (command: `python resolve_one.py <name>`, which calls swebench_unified.harness.run_resolve('astropy__astropy-8707', patch, run_id='geq8707k-<name>'); per-attack JSON in <name>.resolve.json). Refinement used mapping.md §2's bijection (str<->Source.text/List Char, bytes<->Source.raw/List Nat, chr<->Char.ofNat, bytes.decode('latin-1')<->codepointsOf), with site B (header.py) kept GOLD-VERBATIM per refinement.md §B.

OBSERVED RESULTS — all seven RESOLVED, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 11/11 pass: atk_2.patch (oracle echo -> the decode itself)               RESOLVED atk_3.patch (partial-domain guard + else-raise)              RESOLVED atk_4.patch (octets reduced mod 256 first)                   RESOLVED atk_8.patch (foldl-onto-front then reverse)                  RESOLVED atk_12.patch (emptiness dispatch then foldr)                 RESOLVED atk_14.patch (String-carrier round-trip)                     RESOLVED atk_15.patch (imperative while-loop + decreasing measure)    RESOLVED Controls: gold.patch RESOLVED (harness lane healthy); atk_siteA_only.patch (gold card.py hunk ONLY, header.py left at base_commit) RESOLVED — this MECHANIZES refinement.md §B's ungraded-site claim. => No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds.

### ATTACK CLASSES COVERED (all required classes present)
 prepatch bug          atk_1  raw source REFUSED (Except.error rawNotAccepted) -> REJECTED
 ungrounded oracle echo atk_2  `return imageSpec src`, computes nothing -> verifies, patch RESOLVES
 partial domain        atk_3 (guard+refuse), atk_4 (mod 256), atk_18 (guard FALSE on the whole
                       admissible domain = prepatch wearing a guard -> REJECTED), atk_20 (7-bit codec)
 boundary              atk_5 (high octets folded -128), atk_6 (dropLast), atk_7 (empty raw refused),
                       atk_9 (length>80 refused), atk_11 (reversed), atk_16 (octet 255 -> '?'),
                       atk_17 (NUL dropped), atk_19 (trailing space appended) — ALL REJECTED
 control-flow effect   atk_8 (foldl+reverse), atk_12 (emptiness dispatch+foldr),
                       atk_15 (real `while` loop, invariant + `decreasing rest.length`) -> all verify,
                       all patches RESOLVE (correct reshapes, as they should)
 wrong branch          atk_10 text source pushed through the octet decoder -> REJECTED
 omitted-callee probe  atk_13 impl performs the fixed-width padding ITSELF -> REJECTED
 R-leg probe           atk_14 String-carrier round-trip -> verifies, patch RESOLVES

### TWO ATTACKS WORTH SINGLING OUT (the sharpest available, both REJECTED)
 atk_20 CODEC SUBSTITUTION: decodes octets <128 byte-for-byte and REFUSES high octets, exactly as an
 `ascii` codec would. It agrees with the gold patch on the FAIL_TO_PASS witness b"ABC     = 'abc'"
 (pure ASCII) and on all 11 PASS_TO_PASS — so the TEST SUITE CANNOT TELL IT APART from correct. The
 spec rejects it anyway (residual goal `forall x in b, x < 128`). This is the case where the spec is
 STRICTLY STRONGER than the graded oracle, which is the safe direction and the whole point of the
 bundle. Measured: ascii and utf-8 each reject 128/256 octets, so neither is the modeled map.
 atk_19 _pad-COLLISION: my A4 audit found the real _pad is NOT injective — it absorbs trailing spaces
 (_pad('X') == _pad('X ')), 5 collisions between distinct images in 50k samples. So appending a
 trailing space to the decoded image is UNOBSERVABLE after the omitted downstream normalizer. If the
 spec had been stated only up to the post-_pad image, this would verify. It is REJECTED (`|- False`),
 proving the model pins the image PRE-normalization exactly, as refinement.md A4 claims.

### A-LEG AUDIT (my assigned focus; R/I legs are G-CONF's)
A3 codepointsOf <-> bytes.decode('latin-1') (A-REFERENCE, the only deep model). Lean side (ax_check.lean, via lean_verify.sh): (List.range 256).all (fun b => (Char.ofNat b).toNat == b) evaluates `true`, and (codepointsOf (List.range 256)).map Char.toNat == List.range 256 evaluates `true` — Char.ofNat is the identity on code points across the whole 0-255 block and codepointsOf preserves every octet's value in order.

Python side (ax_py.py): re-derived the reference independently — 0 divergences over all 256 single octets, 8 boundary sequences (empty, all-256-in-order, NUL runs, 0xFF runs, UTF-8 byte pairs, the F2P witness), and 20 000 fuzz sequences seeded 8707 (the bundle's pinned seed). latin-1 confirmed total and single-char on all 256 octets, so mapping.md §3.1's "round-trips ALL 256 octet values" claim holds. The A-reference correspondence to the real callee HOLDS. A4 _pad (I-tagged, NOT axiomatized). pad_check.py transliterates the real _pad verbatim from card.py:1268: 0 branch-identity divergences over 200 000 inputs — _pad is a function of the image alone, blind to which branch produced it, so it genuinely cancels out.

Its non-injectivity is the one hazard and atk_19/atk_13 close it from both sides (spec pins the image tighter than _pad can observe = safe direction). Left as the real repo callee, never axiomatized: no dead axiom ships. A-CONSUMED legs: NONE EXIST. grep for `^\s*axiom` in Solution.lean returns nothing, matching the axioms region's self-declaration. So no A-consumed leg can be over-claimed or dead. A1/A2/A5: A1 (isinstance dispatch <-> match on constructor tag) and A2 (text image used as-is) are R/I and hold under the §2 bijection. A5 — the `error` constructor exists only to express the prepatch refusal — is confirmed by atk_1 failing precisely on the raw arm.

PRECONDITION SCOPE (pre_check.py): `require forall x in b, x < 256` is EXACTLY the Python `bytes` type invariant — 0/100 004 real bytes inputs violate it (incl. bytes(range(256)), 1000-byte 0xFF and NUL runs). It excludes NO reachable input, so it grants no partial-domain escape; the text branch is unconditioned (True). atk_18 confirms the vacuity direction is closed. NO KIND-3: every leg is R, A-reference, or I. The one genuinely changed op — accept a raw octet source by decoding it byte-for-byte — sits DEEPLY in the pure region (imageSpec/codepointsOf), not behind an axiom about the function under change. refinement.md §C's claim is accurate.

CROSS-BACKEND NOTE (flagged, NOT transferred). The NAGINI bundle for this same instance is recorded
G-EQ BROKEN: its atk_2 skipped the decode entirely and still verified, because its `reinterpret` was
axiomatized as the IDENTITY (Ensures(Result() == x)), leaving the boolean literal passed to
pad_runtime as the spec's only trace of "was it decoded?". That hole DOES NOT EXIST HERE: velvet
models the decode DEEPLY as codepointsOf (a computed List Char), not as an identity-axiomatized
callee, so `out = imageSpec src` forces the raw arm to produce the per-octet code-point image. I
re-encoded that exact shape as atk_1 (refuse) and atk_18 (guard-false = decode never runs) and both
are REJECTED with residual goals on the raw arm. I did not carry the nagini verdict over — the
mechanism is backend-specific and re-judging it from this lane would invent a finding.

PRIOR PASSES. meta.json records G-EQ INCONCLUSIVE ("only 0 attacks") and G-PANEL-3 quotes an earlier
"atk_5.lean verifies but its patch does not resolve". Neither is reproducible from retained evidence:
the referenced dir is reaped, and the two surviving
velvet G-EQ scratch dirs (mfsbdk_d, ds2drjlj) show every verifying velvet attack RESOLVING
(5/5 and 3/3). ds2drjlj's non-resolving atk_1/atk_5/atk_6 are NAGINI .py attacks, not velvet, and one
of them (atk_6) failed a PASS_TO_PASS test — consistent with the nagini finding above, not this
bundle. I re-derived everything from scratch rather than inheriting any label.

VERDICT: SOUND. 20 admissible same-spec attacks run; positive control verifies; prepatch bug
reproduced and rejected; all 7 verifying impls' faithful patches EXECUTED through the official
harness and all 7 RESOLVED. No verify-but-not-correct witness exists. The A-legs' correspondence to
the real callees holds under independent re-derivation, and refinement.md contains no kind-3 leg.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK ATTACK: no divergence found. Verdict FAITHFUL.

REFERENCE DISCIPLINE. I compared the modeled function against the worktree with patch.diff APPLIED (gold patch applied inside swebench/sweb.eval.x86_64.astropy_1776_astropy-8707 at /testbed, confirmed by echoing the inserted `image = image.decode('latin1')` hunk before every run). Base commit a85a0747 was used ONLY to confirm the prepatch refusal is real, never as the postpatch oracle -- so no part of this verdict treats the patch delta as a divergence.

SPEC REGION INTEGRITY. swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. region_hashes match meta.json G-HYGIENE exactly (axioms b8abf1b4..., pure 97577b1e..., spec_view dca76f74...); only `impl` differs (f684c25e vs 844bcf76), which is correct for a prepatch variant. Solution.lean verifies via scripts/lean_verify.sh (exit 0).

MODELED FUNCTION: buildImage <-> Card.fromstring (card.py:547). Spec: `ensures out = imageSpec src`, imageSpec(text s)=ok s, imageSpec(raw b)=ok (codepointsOf b), require (raw b => forall x in b, x < 256).

DIVERGENCE HUNT (all against the PATCHED repo; model composed with the real I-tagged _pad, since _pad is deliberately excluded from the Lean model and left real in the G-CONF shadow):
  * All 256 single octets, exhaustively: 0 disagreements.
  * Boundary raw: b'', b'\x00', b'\xff', bytes(range(256)), reversed, b"ABC     = 'abc'" (the F2P input), high bytes \x80\x81\xfe\xff, UTF-8 pair \xc3\xa9, surrogate-ish byte pairs \xd8\x00 / \xdb\xff, lengths 79/80/81/160/161, END_CARD: 0 disagreements.
  * Boundary text: '', 'A'*{79,80,81,160}, '\x00', '\xff', 'e-acute', CJK, astral U+1F600, control chars: 0 disagreements.
  * Fuzz: 40k random bytes seqs (len 0-200) + 20k random str (len 0-200, codepoints to 0x2FFF) + a second 20k sweep with len 0-500 and every length 0..399 of b'A'*n: 0 disagreements, 0 unexpected raises.
  Total ~80k+ inputs, zero divergence.

### ATTACKS THAT FAILED TO LAND (each a way the spec could have been TOO STRONG):
  1. "always-ok is over-claimed" -- spec says construction NEVER refuses postpatch. I searched for any str/bytes input where the patched real callee raises: 0 found over ~20k cases incl. all 256 octets and lengths 0..399. latin-1 is total on 0..255 (0 octets fail decode), so the `Except.error` branch being unreachable postpatch is exactly the real behavior, not an over-claim. The `ImageErr.rawNotAccepted` constructor is dead in Solution.lean but is what Solution_prepatch uses to express the refusal -- an unused error constructor makes the modeled function disagree with the real callee on NO input.
  2. "codepointsOf != latin-1" -- Char.ofNat could clamp or hit the surrogate hole. Discharged in Lean: `forall b < 256, (Char.ofNat b).toNat = b` proved by decide (maxRecDepth 100000), so the per-octet map is byte-for-byte latin-1 on the whole domain. Matches the real bytes.decode('latin-1') elementwise on all 256 values.
  3. "require x < 256 is an artificial narrowing" -- no: Python `bytes` elements are 0..255 by type invariant, so the precondition is precisely the R-refinement of the bytes carrier (mapping.md §2), admitting every real input. It excludes nothing the real function accepts.
  4. "prepatch bug is fabricated" -- confirmed real at base: Card.fromstring(b"ABC     = 'abc'") raises TypeError: can't concat str to bytes. Positive control: str input works at base. (Incidental: at base, bytes of length an exact multiple of 80 slip through _pad's early return and are accepted -- but this does NOT weaken the postpatch spec, which I verified agrees with the real patched callee at len 0/80/160/240; and the F2P input len=15 is squarely in the refusing region, so G-DIFF's discrimination is sound.)
  5. "non-str/bytes carriers mis-modeled" -- bytearray and memoryview raise TypeError in the PATCHED repo too (the patch's isinstance(image, bytes) does not cover them). The patch did not fix these, so declining to model them is not over-claiming; they are outside both Source constructors.
  6. "surrogate str diverges" -- real accepts lone surrogates ('\ud800' -> _pad only). Lean Char cannot represent surrogates, so these are unrepresentable in the carrier rather than mis-modeled; no input in the carrier's image disagrees.
  7. "Header.fromstring (site B) omission hides a divergence" -- verified the header site genuinely delegates per-card to the fixed Card.fromstring: Header.fromstring(bytes) == Header.fromstring(same.decode('latin1')) on a synthetic 3-card header. It is also ungraded (test_header_fromstring_bytes is in neither FAIL_TO_PASS nor PASS_TO_PASS -- confirmed against instance.json). Its omission cannot make the modeled function disagree with its own callee.

SCOPE NOTE (not a faithfulness defect, flagged for the panel): excluding _pad makes the spec WEAKER, not stronger -- it is a too-weak/coverage question, not my lane, and the discriminating content still holds (prepatch fails `out = imageSpec src` on the raw clause). meta.json records G-EQ as fail with detail "INCONCLUSIVE -- only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control". That is an audit-harness under-run, not evidence of spec weakness: I independently reproduced the prepatch bug AND its positive control above. Per standing guidance, an inconclusive/under-run gate must not be re-judged as the reject lane.

CONCLUSION: I could not find any input on which the modeled function disagrees with the real patched Card.fromstring. The spec is neither too strong nor drifted from real repo behavior. FAITHFUL -- no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK: leakage / gold-reconstruction. Verdict NO-LEAKAGE.

### Integrity preconditions (both verified)
1. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True — spec regions byte-identical, so the prepatch variant cannot smuggle spec differences.
2. spec_view sha256 = dca76f749b2c24abaa1ef4c8ed23de22f2225445309ee5cee72fc7b9f83ff9e3, exactly matching meta.json gates.G-HYGIENE.data.region_hashes.spec_view — the view I attacked is the view the consumer gets. impl elided, prove_correct body elided (`loom_solve` absent).
3. Confirmed the consumer surface is spec_view + meta.modeled_functions only (eval/prompts.py _spec_block, eval/dataset.py as_dict). refinement.md / mapping.md / patch.diff never reach the solver, so their explicit `latin1` / `Card.fromstring` / `_pad` / `image.decode('latin1')` mentions are audit-only and out of scope. WITHHELD_FIELDS guard covers patch/test_patch/F2P/P2P.

### Mechanical screen
leakage.screen() re-run independently: PASSED, 0 hard failures, 0 warnings. Detail:
- Diff markers: none. Patched paths (astropy/io/fits/card.py, header.py) and dotted module paths: absent.
- Gold changed-line reproduction: I lowered the gate threshold from len>=8 to len>=4; only hits are the bare token 'True' (from the docstring doctest lines), which is content-free. Longest common normalized substring between ALL gold added-lines and the spec view is 13 chars: 'charactersare' — English prose collision, carries no edit.
- _patch_changed_symbols(gold) == {'fromstring'} — and 'fromstring' IS in the public problem_statement (`Header.fromstring`, `Card.fromstring` both named verbatim). So the single screened symbol is already public; the exemption is legitimate, not a gate loophole.
- Narration vocabulary: clean. Notably the author avoided the trap of writing 'fix'/'bug'/'previously' in the pure-region measure comments.
- Gold-edit vocabulary absent from spec view: latin / latin1 / latin-1 / iso-8859 / decode / isinstance / _pad / pad / mojibake / ascii / astropy / fits / card / header / fromstring / sep / end_card / doctest — ALL absent. De-narration is thorough: the codec is called 'the per-octet code-point interpretation', _pad is 'the unchanged downstream fixed-width normalizer', bytes is 'a raw octet sequence'.

### The one real candidate leak, and why it fails to be one
The spec view DOES pin the byte->character mapping semantically: `Char.ofNat b` per octet, plus the prose 'each octet is mapped to the character whose code point equals that octet's value ... byte-for-byte, with no re-encoding' and `require ∀ x ∈ b, x < 256`. Latin-1 is the unique standard codec that is both total on 0–255 and code-point-identical, so this determines the codec up to aliasing WITHOUT naming it. The problem_statement never names a codec (it says only 'accept unicode or bytes string types'). That is a genuine marginal information increment over the public issue, and it is the strongest available leakage argument. I pursued it two ways and it does not survive either:

(a) BLIND RECONSTRUCTION FROM THE PUBLIC ISSUE ALONE. A probe given only the problem_statement (no repo, no spec, no hints) independently produced the gold patch essentially verbatim: `if isinstance(image, bytes): image = image.decode('latin1')` inserted after `card = cls()` and BEFORE `_pad(image)`, in astropy/io/fits/card.py Card.fromstring, plus the parallel header.py edit and the `data : str or bytes` docstring change. It assigned latin-1 ~60% unprompted, reasoning from FITS's 'keep pathological bytes rather than raising' posture. So file, function, edit shape, insertion point, and even the codec are already reconstructible from the solver-visible issue. The spec view raises latin-1 confidence (~60% -> high) but does not disclose anything the issue does not already imply.

(b) THE PINNED DISCRIMINATOR IS NOT GRADEABLE — decisive. I substituted four non-gold codecs for the gold decode line in the real SWE-bench eval image (swebench/sweb.eval.x86_64.astropy_1776_astropy-8707), test_patch applied, and ran the full graded set (1 FAIL_TO_PASS + 11 PASS_TO_PASS):
    latin1 (gold)        -> 12 passed
    ascii                -> 12 passed
    utf-8                -> 12 passed
    cp1252               -> 12 passed
    utf-8 errors=replace -> 12 passed
All five pass 12/12. The F2P test is `Card.fromstring(b"ABC     = 'abc'")` — pure ASCII — so every codec agrees on the graded input. The codec choice is therefore behaviorally invisible to grading. Even granting full reconstruction of the codec from the spec view, it converts to exactly zero grading advantage. A leak that cannot move the grade is not gold-reconstruction; it is faithful specification of behavior the tests happen not to discriminate.

Additionally, this pin is compelled by faithfulness, not gratuitous: `ensures out = imageSpec src` must be total and deterministic, so ANY correct spec of 'accept a raw octet source' has to say which characters result. Removing it would leave the postcondition ungroundable (spec_guide directive 8) and would hand G-PANEL-1 a trivial vacuity attack. No relaxed-leakage exemption is needed here — the leak vocabulary is fully de-narrated, so meta.json gates.G-LEAK.status = pass (not 'relaxed') is the correct classification.

### Minor observations (not findings)
- The word 'image' appears in the spec view ('character image', identifiers `buildImage`/`imageSpec`) and not in the problem_statement; it coincides with the gold patch's parameter name `image`. Not a leak: 'card image' is public astropy/FITS domain vocabulary already in Card.fromstring's pre-existing docstring, the screened identifier is `buildImage` not `image`, parameter names are outside _patch_changed_symbols by design (def/class only), and localization is already fully public since the issue names Card.fromstring outright.
- `ImageErr.rawNotAccepted` describes the pre-patch refusal, but abstractly ('a raw octet sequence is rejected instead of being accepted') with no mention of TypeError, _pad, or str+bytes concatenation — the failure MECHANISM is withheld. Naming the refusal outcome is required to make the postcondition discriminating; it narrates the desired behavior, not the diagnosis.
- Out of my gate, but flagging per bundle hygiene: meta.json records G-EQ and G-PANEL-1 as fail with detail 'INCONCLUSIVE — only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control'. Zero attacks launched is the signature of an agent-launch/host-saturation outage, not a demonstrated spec defect; those two cells should be bucketed by reason and re-run rather than read as findings. My own verdict is independent of them.

Confidence: high. The mechanical screen passes at a threshold I tightened by hand, the gold edit is reconstructible from the public issue alone, and the sole piece of information the spec view adds beyond the issue is empirically worth nothing at grading time across four codec substitutions.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.