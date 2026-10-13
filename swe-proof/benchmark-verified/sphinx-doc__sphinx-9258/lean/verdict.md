# P2 adversarial audit — sphinx-doc__sphinx-9258

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -156,11 +156,11 @@
 
 -- impl-start
 def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do
-  let subTargets := reSplit true target
+  let subTargets := reSplit false target
   let mut results : List Seg := []
   for sub in subTargets do
     if sub ≠ [] then
-      if (delimLen true sub).isSome then
+      if (delimLen false sub).isSome then
         results := results ++ [Seg.sep sub]
       else
         results := results ++ [Seg.name sub]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -159,11 +159,10 @@
   let subTargets := reSplit true target
   let mut results : List Seg := []
   for sub in subTargets do
-    if sub ≠ [] then
-      if (delimLen true sub).isSome then
-        results := results ++ [Seg.sep sub]
-      else
-        results := results ++ [Seg.name sub]
+    if (delimLen true sub).isSome then
+      results := results ++ [Seg.sep sub]
+    else
+      results := results ++ [Seg.name sub]
   return results
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -161,9 +161,9 @@
   for sub in subTargets do
     if sub ≠ [] then
       if (delimLen true sub).isSome then
+        results := results ++ [Seg.name sub]
+      else
         results := results ++ [Seg.sep sub]
-      else
-        results := results ++ [Seg.name sub]
   return results
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -160,10 +160,7 @@
   let mut results : List Seg := []
   for sub in subTargets do
     if sub ≠ [] then
-      if (delimLen true sub).isSome then
-        results := results ++ [Seg.sep sub]
-      else
-        results := results ++ [Seg.name sub]
+      results := results ++ [Seg.name sub]
   return results
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -161,9 +161,9 @@
   for sub in subTargets do
     if sub ≠ [] then
       if (delimLen true sub).isSome then
-        results := results ++ [Seg.sep sub]
+        results := [Seg.sep sub] ++ results
       else
-        results := results ++ [Seg.name sub]
+        results := [Seg.name sub] ++ results
   return results
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -164,7 +164,7 @@
         results := results ++ [Seg.sep sub]
       else
         results := results ++ [Seg.name sub]
-  return results
+  return results.drop 1
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -156,15 +156,8 @@
 
 -- impl-start
 def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do
-  let subTargets := reSplit true target
-  let mut results : List Seg := []
-  for sub in subTargets do
-    if sub ≠ [] then
-      if (delimLen true sub).isSome then
-        results := results ++ [Seg.sep sub]
-      else
-        results := results ++ [Seg.name sub]
-  return results
+  let _ := reSplit true target
+  return ([] : List Seg)
 -- impl-end
 
 -- proof-start
@@ -173,54 +166,10 @@
       problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by
   intro target
   show implementation_splitTypeSpec target = tokenize target
-  unfold implementation_splitTypeSpec tokenize
-  generalize reSplit true target = l
-  suffices h : ∀ (acc : List Seg),
-      (forIn (m := Id) l acc (fun sub r =>
-        if sub ≠ [] then
-          if (delimLen true sub).isSome = true then
-            pure (ForInStep.yield (r ++ [Seg.sep sub]))
-          else pure (ForInStep.yield (r ++ [Seg.name sub]))
-        else pure (ForInStep.yield r))) =
-        acc ++ (l.filter (· ≠ [])).map classifySeg by
-    have := h []
-    simpa using this
-  induction l with
-  | nil => intro acc; simp; rfl
-  | cons a t ih =>
-      intro acc
-      simp only [List.forIn_cons, List.filter_cons]
-      by_cases h : a ≠ []
-      · have hd' : decide (a ≠ []) = true := decide_eq_true h
-        rw [if_pos h, if_pos hd']
-        by_cases hd : (delimLen true a).isSome = true
-        · rw [if_pos hd]
-          show (forIn (m := Id) t (acc ++ [Seg.sep a]) _) = _
-          rw [ih (acc ++ [Seg.sep a])]
-          have hcl : classifySeg a = Seg.sep a := by
-            unfold classifySeg
-            rw [Option.isSome_iff_exists] at hd
-            obtain ⟨w, hw⟩ := hd
-            rw [hw]
-          rw [List.map_cons, hcl]
-          simp
-        · rw [if_neg hd]
-          show (forIn (m := Id) t (acc ++ [Seg.name a]) _) = _
-          rw [ih (acc ++ [Seg.name a])]
-          have hcl : classifySeg a = Seg.name a := by
-            unfold classifySeg
-            have : delimLen true a = none := by
-              cases hcase : delimLen true a with
-              | none => rfl
-              | some v => rw [hcase] at hd; simp at hd
-            rw [this]
-          rw [List.map_cons, hcl]
-          simp
-      · have hd' : decide (a ≠ []) = false := by
-          simp only [decide_eq_false_iff_not, not_not] at *
-          simpa using h
-        rw [if_neg h, hd']
-        show (forIn (m := Id) t acc _) = _
-        rw [ih acc]
-        simp
+  first
+  | rfl
+  | (unfold implementation_splitTypeSpec tokenize; rfl)
+  | (unfold implementation_splitTypeSpec tokenize; simp)
+  | (simp [implementation_splitTypeSpec, tokenize])
+  | (unfold implementation_splitTypeSpec; simp [tokenize])
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a parameter/attribute type specification into the pieces that should
be cross-referenced as type names versus the pieces that are mere separators.

A type specification written in a documentation field (for example the text
after `:type age:`) may name several alternative types joined by punctuation and
keywords. The specification string is tokenised left-to-right into a sequence of
segments, alternating free text and separators, in the manner of a regular
splitting operation whose separator is the following alternation (tried in this
order at each position):

* optional surrounding whitespace around one of the bracket/parenthesis/comma
  characters `[ ] ( ) ,`, where the closing side may additionally absorb a
  following `or` keyword;
* the word `or` surrounded by whitespace;
* a vertical bar `|` with optional surrounding whitespace;
* an ellipsis `...`.

After splitting, the empty pieces are discarded. Each surviving piece is then
classified: a piece that is itself a separator (its front matches the separator
alternation) is kept verbatim as separator text; every other piece is a type
name to be cross-referenced. The result lists these classified segments in
order.

The desired behaviour treats a vertical bar `|` (optionally padded by
whitespace) as one of the separators, so that a specification such as
`int | str` yields the two type names `int` and `str` around a `|` separator,
matching the alternatives already available with the `or` keyword.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- recognition and the split are modeled DEEPLY over the observable input string
-- (a list of characters), so no `opaque`/`axiom` callee contract is needed. The
-- downstream, unchanged step that turns each classified segment into a rendered
-- node is a structural one-to-one map and is represented directly by the segment
-- carrier below.
-- axioms-end

-- pure-start
/-- A classified piece of a split type specification: either separator text kept
verbatim, or a type name to be cross-referenced. -/
inductive Seg where
  | sep  : List Char → Seg
  | name : List Char → Seg
deriving DecidableEq, Repr

/-- Whitespace characters recognised by the separator matcher: exactly the code
points the splitting operation treats as whitespace (ASCII whitespace including
vertical tab and form feed, the information-separator controls, NEL, NBSP, and
the Unicode space/line/paragraph separators). -/
def isSp (c : Char) : Bool :=
  let n := c.toNat
  decide ((0x9 ≤ n ∧ n ≤ 0xD) ∨ (0x1C ≤ n ∧ n ≤ 0x20) ∨ n = 0x85 ∨ n = 0xA0 ∨
    n = 0x1680 ∨ (0x2000 ≤ n ∧ n ≤ 0x200A) ∨ n = 0x2028 ∨ n = 0x2029 ∨
    n = 0x202F ∨ n = 0x205F ∨ n = 0x3000)

/-- The bracket / parenthesis / comma characters that may act as separators. -/
def isBracket (c : Char) : Bool :=
  c == '[' || c == ']' || c == '(' || c == ')' || c == ','

/-- Length of the leading run of whitespace. -/
def spacesLen : List Char → Nat
  | []      => 0
  | c :: cs => if isSp c then 1 + spacesLen cs else 0

/-- Ellipsis alternative: `...` matches three characters. -/
def dotsLen (cs : List Char) : Option Nat :=
  match cs with
  | '.' :: '.' :: '.' :: _ => some 3
  | _ => none

/-- Vertical-bar alternative (`\s*\|\s*`), then the ellipsis alternative. The
`pipe` flag selects whether the vertical bar participates. -/
def pipeOrDots (pipe : Bool) (cs : List Char) : Option Nat :=
  if pipe then
    let k := spacesLen cs
    match cs.drop k with
    | '|' :: _ => some (k + 1 + spacesLen (cs.drop (k + 1)))
    | _        => dotsLen cs
  else dotsLen cs

/-- The `or`-keyword alternative (`\s+or\s+`), then the vertical bar / ellipsis
alternatives. -/
def tailDelim (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | 'o' :: 'r' :: tl =>
    if k ≥ 1 ∧ spacesLen tl ≥ 1 then some (k + 2 + spacesLen tl)
    else pipeOrDots pipe cs
  | _ => pipeOrDots pipe cs

/-- Match the whole separator alternation as a prefix of `cs`, returning the
length consumed, or `none` if no alternative matches at the front. The first
alternative is `\s*[\[\]\(\),](?:\s*or\s)?\s*` (optional whitespace around a
bracket-class character, the closing side optionally absorbing a following
`or`); the remaining alternatives follow in `tailDelim`. -/
def delimLen (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | c :: _ =>
    if isBracket c then
      let b := k + 1
      let k2 := spacesLen (cs.drop b)
      let j := b + k2
      match cs.drop j with
      | 'o' :: 'r' :: c3 :: _ =>
        if isSp c3 then some (j + 3 + spacesLen (cs.drop (j + 3)))
        else some (b + spacesLen (cs.drop b))
      | _ => some (b + spacesLen (cs.drop b))
    else tailDelim pipe cs
  | [] => tailDelim pipe cs

/-- Split a character list the way a regular splitting operation with a capturing
separator does: emit alternating free-text and separator pieces (including empty
pieces), consuming a separator whenever the alternation matches at the current
position and otherwise accumulating one character of free text. `fuel` bounds the
recursion; the wrapper below supplies `target.length`, which always suffices. -/
def reSplitFuel (pipe : Bool) : Nat → List Char → List Char → List (List Char)
  | 0,        cur, _        => [cur]
  | (_ + 1),  cur, []       => [cur]
  | (fuel+1), cur, c :: rest =>
    match delimLen pipe (c :: rest) with
    | some n =>
        let s := c :: rest
        cur :: (s.take n) :: reSplitFuel pipe fuel [] (s.drop n)
    | none => reSplitFuel pipe fuel (cur ++ [c]) rest

/-- The split of `target` into alternating text/separator pieces (with empties). -/
def reSplit (pipe : Bool) (target : List Char) : List (List Char) :=
  reSplitFuel pipe target.length [] target

/-- Classify a nonempty split piece: a piece whose front matches the separator
alternation is separator text; otherwise it is a type name. -/
def classifySeg (piece : List Char) : Seg :=
  match delimLen true piece with
  | some _ => Seg.sep piece
  | none   => Seg.name piece

/-- Tokenise a type specification into classified segments: split, drop empty
pieces, classify each survivor. The vertical bar participates as a separator. -/
def tokenize (target : List Char) : List Seg :=
  ((reSplit true target).filter (· ≠ [])).map classifySeg
-- pure-end

-- post-conditions-start
/-- The result is exactly the classified-segment tokenisation of the type
specification, with the vertical bar recognised as a separator alongside the
brackets, commas, the `or` keyword and the ellipsis. -/
def problem_spec_splitTypeSpec (target : List Char) (result : List Seg) : Prop :=
  result = tokenize target
-- post-conditions-end

-- impl-start
def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do
  return tokenize target
-- impl-end

-- proof-start
theorem correct_splitTypeSpec :
    ∀ (target : List Char),
      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by
  intro target
  show implementation_splitTypeSpec target = tokenize target
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: problem_spec_splitTypeSpec target result := (result = tokenize target) — a DEFINITIONAL, TIGHT postcondition that uniquely pins the output for every input over the fully-grounded pure-region deep model (spacesLen/delimLen/reSplit/classifySeg/tokenize). meta.json confirms "axioms": [] and "deep_model_references": [] — NO A-legs (no opaque/axiom callee, no deep-model reference). Consequently ANY impl whose proof of ∀target, impl target = tokenize target closes with clean axioms must be extensionally EQUAL to tokenize (= gold post-patch behaviour); there is no partial-domain / ungrounded-oracle / axiom-consumption escape. => No wrong impl can close, so protocol step 2 (materialize + resolve faithful patch for every closing wrong impl) has ZERO candidates; nothing can exhibit verify⇏correct.

ATTACK BATTERY (7 distinct same-spec wrong impls; each edits ONLY the impl region, reusing gold structured proof for atk_1..6 and an auto-proof for atk_7; verifications run concurrently ≤4 at a time via scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug / partial-domain): reSplit false / delimLen false — omits the \s*\|\s* alternative; diverges on 'int | str' (keeps it one name). lean_verify exit=1 (Type mismatch @187:4). This IS the recorded prepatch variant; prepatch reproduced.
- atk_2 (boundary): drops the empty-piece filter; diverges on 'x[y], z' (emits a spurious empty ('name','')). exit=1 (Type mismatch @186:4).
- atk_3 (classification swap): sep/name swapped; diverges on 'int | str'. exit=1 (Type mismatch @187:4).
- atk_4 (ungrounded-oracle / degenerate classify): every survivor tagged Seg.name; diverges on separators. exit=1 (Type mismatch @184:4).
- atk_5 (control-flow-effect): prepend instead of append (reversed order); diverges on ≥2 segments. exit=1 (Type mismatch @187:4).
- atk_6 (partial-domain / off-by-one): results.drop 1 drops first surviving segment; diverges on 'int | str'. exit=1 (Type mismatch @187:4).
- atk_7 (ungrounded-oracle echo, wrong): returns []; diverges on any nonempty tokenize. exit=1 (unsolved goals @166:81).
All 7 divergences from tokenize independently confirmed via the Python shadow (conformance_check.lean_tokenize). None verifies => none closes with clean axioms => no faithful patch to resolve (patches={}).

POSITIVE CONTROL: pos_control.lean (impl := tokenize target, proof by rfl) — lean_verify exit=0; #print axioms correct_splitTypeSpec => 'does not depend on any axioms' (clean, no sorryAx). Confirms the spec is satisfiable by a genuine same-spec impl and the harness would accept a correct alternative.

Exact commands: python -c '...same_spec...' (lean backend) => True for all 8; bash scripts/lean_verify.sh <file>.lean. Results: atk_1..7 exit=1; pos_control exit=0; pos_axcheck (#print axioms appended) exit=0 with 'does not depend on any axioms'.

REFINEMENT AUDIT (§4): refinement.md legs 1-6 are all R (1,2,4,5) / I (3,6); deep-model rows (delimLen tower, reSplit, classifySeg, tokenize) tagged R (deep model). No kind-3 leg, no A-consumed/A-reference. G-AX skips (empty axioms region). R/I legs are mechanically discharged by G-CONF: Python replica of the Lean model diffed against the real post-patch re.split+classify (NEW pattern) and cross-checked vs direct re.split for BOTH NEW and OLD patterns over ≥1e5 fuzzed inputs incl. non-ASCII \s code points (isSp verified == Python \s over all Unicode). No A-leg correspondence to audit (none exist). mapping.md base_commit symbol binding matches worktree sphinx/domains/python.py:304-324 (make_xrefs; delims @307).

Conclusion: verify⇒correct holds for this bundle — the tight definitional spec over a fully-grounded, A-free model leaves no room for a clean-axiom proof of a divergent impl. ≥5 (7) attacks run, positive control verifies clean, prepatch reproduced. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

/-!
Splitting a parameter/attribute type specification into the pieces that should
be cross-referenced as type names versus the pieces that are mere separators.

A type specification written in a documentation field (for example the text
after `:type age:`) may name several alternative types joined by punctuation and
keywords. The specification string is tokenised left-to-right into a sequence of
segments, alternating free text and separators, in the manner of a regular
splitting operation whose separator is the following alternation (tried in this
order at each position):

* optional surrounding whitespace around one of the bracket/parenthesis/comma
  characters `[ ] ( ) ,`, where the closing side may additionally absorb a
  following `or` keyword;
* the word `or` surrounded by whitespace;
* a vertical bar `|` with optional surrounding whitespace;
* an ellipsis `...`.

After splitting, the empty pieces are discarded. Each surviving piece is then
classified: a piece that is itself a separator (its front matches the separator
alternation) is kept verbatim as separator text; every other piece is a type
name to be cross-referenced. The result lists these classified segments in
order.

The desired behaviour treats a vertical bar `|` (optionally padded by
whitespace) as one of the separators, so that a specification such as
`int | str` yields the two type names `int` and `str` around a `|` separator,
matching the alternatives already available with the `or` keyword.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- recognition and the split are modeled DEEPLY over the observable input string
-- (a list of characters), so no `opaque`/`axiom` callee contract is needed. The
-- downstream, unchanged step that turns each classified segment into a rendered
-- node is a structural one-to-one map and is represented directly by the segment
-- carrier below.
-- axioms-end

-- pure-start
/-- A classified piece of a split type specification: either separator text kept
verbatim, or a type name to be cross-referenced. -/
inductive Seg where
  | sep  : List Char → Seg
  | name : List Char → Seg
deriving DecidableEq, Repr

/-- Whitespace characters recognised by the separator matcher: exactly the code
points the splitting operation treats as whitespace (ASCII whitespace including
vertical tab and form feed, the information-separator controls, NEL, NBSP, and
the Unicode space/line/paragraph separators). -/
def isSp (c : Char) : Bool :=
  let n := c.toNat
  decide ((0x9 ≤ n ∧ n ≤ 0xD) ∨ (0x1C ≤ n ∧ n ≤ 0x20) ∨ n = 0x85 ∨ n = 0xA0 ∨
    n = 0x1680 ∨ (0x2000 ≤ n ∧ n ≤ 0x200A) ∨ n = 0x2028 ∨ n = 0x2029 ∨
    n = 0x202F ∨ n = 0x205F ∨ n = 0x3000)

/-- The bracket / parenthesis / comma characters that may act as separators. -/
def isBracket (c : Char) : Bool :=
  c == '[' || c == ']' || c == '(' || c == ')' || c == ','

/-- Length of the leading run of whitespace. -/
def spacesLen : List Char → Nat
  | []      => 0
  | c :: cs => if isSp c then 1 + spacesLen cs else 0

/-- Ellipsis alternative: `...` matches three characters. -/
def dotsLen (cs : List Char) : Option Nat :=
  match cs with
  | '.' :: '.' :: '.' :: _ => some 3
  | _ => none

/-- Vertical-bar alternative (`\s*\|\s*`), then the ellipsis alternative. The
`pipe` flag selects whether the vertical bar participates. -/
def pipeOrDots (pipe : Bool) (cs : List Char) : Option Nat :=
  if pipe then
    let k := spacesLen cs
    match cs.drop k with
    | '|' :: _ => some (k + 1 + spacesLen (cs.drop (k + 1)))
    | _        => dotsLen cs
  else dotsLen cs

/-- The `or`-keyword alternative (`\s+or\s+`), then the vertical bar / ellipsis
alternatives. -/
def tailDelim (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | 'o' :: 'r' :: tl =>
    if k ≥ 1 ∧ spacesLen tl ≥ 1 then some (k + 2 + spacesLen tl)
    else pipeOrDots pipe cs
  | _ => pipeOrDots pipe cs

/-- Match the whole separator alternation as a prefix of `cs`, returning the
length consumed, or `none` if no alternative matches at the front. The first
alternative is `\s*[\[\]\(\),](?:\s*or\s)?\s*` (optional whitespace around a
bracket-class character, the closing side optionally absorbing a following
`or`); the remaining alternatives follow in `tailDelim`. -/
def delimLen (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | c :: _ =>
    if isBracket c then
      let b := k + 1
      let k2 := spacesLen (cs.drop b)
      let j := b + k2
      match cs.drop j with
      | 'o' :: 'r' :: c3 :: _ =>
        if isSp c3 then some (j + 3 + spacesLen (cs.drop (j + 3)))
        else some (b + spacesLen (cs.drop b))
      | _ => some (b + spacesLen (cs.drop b))
    else tailDelim pipe cs
  | [] => tailDelim pipe cs

/-- Split a character list the way a regular splitting operation with a capturing
separator does: emit alternating free-text and separator pieces (including empty
pieces), consuming a separator whenever the alternation matches at the current
position and otherwise accumulating one character of free text. `fuel` bounds the
recursion; the wrapper below supplies `target.length`, which always suffices. -/
def reSplitFuel (pipe : Bool) : Nat → List Char → List Char → List (List Char)
  | 0,        cur, _        => [cur]
  | (_ + 1),  cur, []       => [cur]
  | (fuel+1), cur, c :: rest =>
    match delimLen pipe (c :: rest) with
    | some n =>
        let s := c :: rest
        cur :: (s.take n) :: reSplitFuel pipe fuel [] (s.drop n)
    | none => reSplitFuel pipe fuel (cur ++ [c]) rest

/-- The split of `target` into alternating text/separator pieces (with empties). -/
def reSplit (pipe : Bool) (target : List Char) : List (List Char) :=
  reSplitFuel pipe target.length [] target

/-- Classify a nonempty split piece: a piece whose front matches the separator
alternation is separator text; otherwise it is a type name. -/
def classifySeg (piece : List Char) : Seg :=
  match delimLen true piece with
  | some _ => Seg.sep piece
  | none   => Seg.name piece

/-- Tokenise a type specification into classified segments: split, drop empty
pieces, classify each survivor. The vertical bar participates as a separator. -/
def tokenize (target : List Char) : List Seg :=
  ((reSplit true target).filter (· ≠ [])).map classifySeg
-- pure-end

-- post-conditions-start
/-- The result is exactly the classified-segment tokenisation of the type
specification, with the vertical bar recognised as a separator alongside the
brackets, commas, the `or` keyword and the ellipsis. -/
def problem_spec_splitTypeSpec (target : List Char) (result : List Seg) : Prop :=
  result = tokenize target
-- post-conditions-end

-- impl-start
def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do
  return tokenize target
-- impl-end

-- proof-start
theorem correct_splitTypeSpec :
    ∀ (target : List Char),
      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by
  intro target
  show implementation_splitTypeSpec target = tokenize target
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: problem_spec_splitTypeSpec target result := (result = tokenize target) — a DEFINITIONAL, TIGHT postcondition that uniquely pins the output for every input over the fully-grounded pure-region deep model (spacesLen/delimLen/reSplit/classifySeg/tokenize). meta.json confirms "axioms": [] and "deep_model_references": [] — NO A-legs (no opaque/axiom callee, no deep-model reference). Consequently ANY impl whose proof of ∀target, impl target = tokenize target closes with clean axioms must be extensionally EQUAL to tokenize (= gold post-patch behaviour); there is no partial-domain / ungrounded-oracle / axiom-consumption escape. => No wrong impl can close, so protocol step 2 (materialize + resolve faithful patch for every closing wrong impl) has ZERO candidates; nothing can exhibit verify⇏correct.

ATTACK BATTERY (7 distinct same-spec wrong impls; each edits ONLY the impl region, reusing gold structured proof for atk_1..6 and an auto-proof for atk_7; verifications run concurrently ≤4 at a time via scripts/lean_verify.sh <file>):
- atk_1 (prepatch bug / partial-domain): reSplit false / delimLen false — omits the \s*\|\s* alternative; diverges on 'int | str' (keeps it one name). lean_verify exit=1 (Type mismatch @187:4). This IS the recorded prepatch variant; prepatch reproduced.
- atk_2 (boundary): drops the empty-piece filter; diverges on 'x[y], z' (emits a spurious empty ('name','')). exit=1 (Type mismatch @186:4).
- atk_3 (classification swap): sep/name swapped; diverges on 'int | str'. exit=1 (Type mismatch @187:4).
- atk_4 (ungrounded-oracle / degenerate classify): every survivor tagged Seg.name; diverges on separators. exit=1 (Type mismatch @184:4).
- atk_5 (control-flow-effect): prepend instead of append (reversed order); diverges on ≥2 segments. exit=1 (Type mismatch @187:4).
- atk_6 (partial-domain / off-by-one): results.drop 1 drops first surviving segment; diverges on 'int | str'. exit=1 (Type mismatch @187:4).
- atk_7 (ungrounded-oracle echo, wrong): returns []; diverges on any nonempty tokenize. exit=1 (unsolved goals @166:81).
All 7 divergences from tokenize independently confirmed via the Python shadow (conformance_check.lean_tokenize). None verifies => none closes with clean axioms => no faithful patch to resolve (patches={}).

POSITIVE CONTROL: pos_control.lean (impl := tokenize target, proof by rfl) — lean_verify exit=0; #print axioms correct_splitTypeSpec => 'does not depend on any axioms' (clean, no sorryAx). Confirms the spec is satisfiable by a genuine same-spec impl and the harness would accept a correct alternative.

Exact commands: python -c '...same_spec...' (lean backend) => True for all 8; bash scripts/lean_verify.sh <file>.lean. Results: atk_1..7 exit=1; pos_control exit=0; pos_axcheck (#print axioms appended) exit=0 with 'does not depend on any axioms'.

REFINEMENT AUDIT (§4): refinement.md legs 1-6 are all R (1,2,4,5) / I (3,6); deep-model rows (delimLen tower, reSplit, classifySeg, tokenize) tagged R (deep model). No kind-3 leg, no A-consumed/A-reference. G-AX skips (empty axioms region). R/I legs are mechanically discharged by G-CONF: Python replica of the Lean model diffed against the real post-patch re.split+classify (NEW pattern) and cross-checked vs direct re.split for BOTH NEW and OLD patterns over ≥1e5 fuzzed inputs incl. non-ASCII \s code points (isSp verified == Python \s over all Unicode). No A-leg correspondence to audit (none exist). mapping.md base_commit symbol binding matches worktree sphinx/domains/python.py:304-324 (make_xrefs; delims @307).

Conclusion: verify⇒correct holds for this bundle — the tight definitional spec over a fully-grounded, A-free model leaves no room for a clean-axiom proof of a divergent impl. ≥5 (7) attacks run, positive control verifies clean, prepatch reproduced. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function (problem_spec_splitTypeSpec := result = tokenize target) and the real post-patch PyXrefMixin.make_xrefs classification (re.split with NEW delims r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)' + per-piece delims_re.match), so the spec is neither too strong nor drifted. Evidence: Gold patch confirmed = the single added \s*\|\s* alternative to delims (patch.diff, matches conformance_check NEW_DELIMS verbatim; base worktree shows the OLD regex). (2) Solution.lean compiles clean via lean_verify.sh (exit 0); #print axioms correct_splitTypeSpec = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is real. (3) same_spec(Solution.lean, Solution_prepatch.lean, lean)=True: spec region byte-identical / impl-independent; meta G-HYGIENE region hashes consistent. (4) isSp verified equal to Python re \s over ALL 0x110000 Unicode code points (0 mismatches) — deep whitespace model exact. (5) Independent differential fuzz beyond the pinned seed: exhaustive over rich alphabet 'ab |[](),.or\t\n' to length 5 (0 diffs) + 2,000,000 random samples over a wider alphabet incl. \f,\v,NBSP,NEL,IDEOGRAPHIC SPACE,FS/GS controls, lengths 0-24 (0 diffs) for lean_re_split(True)==NEW.split, lean_re_split(False)==OLD.split, and lean_tokenize==real post-patch classify. (6) Closed the transliteration gap: ran #eval tokenize in ACTUAL Lean on 12 adversarial inputs ('int | str','x[y], z','a...b','  |  ','a|b|c','[or ]x',' or or ','a , or b','x[ or ]y','||','a| b','int or str') — every output matches the real post-patch re.split+delims_re.match byte-for-byte, including subtle bracket-absorbs-or cases ([or ]x -> sep '[or ',sep ']',name 'x') and ' or or ' -> sep ' or ',name 'or '. The spec is definitional over a fully-grounded DEEP model of the changed op; the unchanged downstream node construction (contnode/innernode vs make_xref) is orthogonal to the fix and faithfully represented by the Seg carrier. No unmodeled behavior, no over-strong constraint, no divergence found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for sphinx-doc__sphinx-9258 (lean).

Mechanical checks: same_spec(Solution.lean, Solution_prepatch.lean)=True via lean backend (spec region byte-identical, impl-independent); meta G-HYGIENE/region_hashes spec_view consistent; recorded G-VERIFY axioms = {propext, Classical.choice, Quot.sound} (no sorryAx, proof genuine); meta G-LEAK = pass (spec view clean).

Gold edit: a single added regex alternative `\s*\|\s*` to `delims` in PyXrefMixin.make_xrefs (sphinx/domains/python.py:307), i.e. treat a whitespace-padded vertical bar `|` as a union-type separator so `int | str` -> two linked type names.

Public disclosure: the problem_statement is literally titled '[RFE] Support union types specification using | (vertical bar/pipe)' and gives the worked example `bytes | str` yielding multiple linked types. It fully and publicly discloses the entire intent of the fix (support `|` as a union separator).

Every spec-view line that touches the edit is a restatement of behavior the public problem_statement already requests, not information sourced from hints_text or the diff:
- docstring bullet 'a vertical bar `|` with optional surrounding whitespace';
- paragraph 'treats a vertical bar `|` (optionally padded by whitespace) as one of the separators, so that a specification such as `int | str` yields the two type names `int` and `str` around a `|` separator, matching the alternatives already available with the `or` keyword';
- the `pipeOrDots` / `delimLen true` `|` branch in the pure region.

The 'optional surrounding whitespace' and 'like the `or` keyword' framing are natural refinements of the public RFE, not privileged detail. The spec view names no Python file/symbol/line and quotes no verbatim in-code regex; the other separators it describes (brackets `[ ] ( )`, comma, `or`, ellipsis) are pre-existing UNCHANGED behavior surrounding the edit, not the gold edit itself, so describing them does not leak. Nothing in the spec view reconstructs the gold edit beyond what problem_statement already states publicly. Consistent with recorded G-LEAK/G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
