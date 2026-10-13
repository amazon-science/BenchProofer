# P2 adversarial audit — django__django-13112

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_1agg.lean`, `atk_3agg.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_modelRef fully pins the output on BOTH branches ('.'∈chars and '.'∉chars) over the entire RefToken domain, so every behaviorally-different impl yields a provably-false equality goal that no sound tactic closes.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,14 +95,7 @@
 
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
-  if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
-  else
-    -- bare name: lowercase the whole token
-    return t.chars.map Char.toLower
+  return t.chars.map Char.toLower
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,10 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
     let prefixPart := prefixSeg t.chars
     let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixPart.map Char.toLower ++ '.' :: namePart.map Char.toLower
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,8 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return t.chars
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,10 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
     let prefixPart := prefixSeg t.chars
     let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return namePart.map Char.toLower ++ '.' :: prefixPart
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,10 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
     let prefixPart := prefixSeg t.chars
     let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixPart ++ namePart.map Char.toLower
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,10 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
     let prefixPart := prefixSeg t.chars
     let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixPart ++ '.' :: namePart
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,13 +96,9 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower
   else
-    -- bare name: lowercase the whole token
-    return t.chars.map Char.toLower
+    return t.chars
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,8 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixSeg t.chars ++ (t.chars.dropWhile (· ≠ '.')).map Char.toLower
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
```

Attack 9 — `atk_5.lean` → not a counterexample (changed the spec)

```diff
@@ -96,12 +96,8 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
 
@@ -117,3 +113,5 @@
   · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩
     simp only [Id.run, h, if_false, pure]
 -- proof-end
+
+#print axioms correct_modelRef
```

Attack 10 — `atk_1agg.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,25 +95,18 @@
 
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
-  if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
-  else
-    -- bare name: lowercase the whole token
-    return t.chars.map Char.toLower
+  return t.chars.map Char.toLower
 -- impl-end
-
 -- proof-start
 theorem correct_modelRef :
     ∀ (t : RefToken),
       problem_spec_modelRef t (implementation_modelRef t) := by
   intro t
   unfold problem_spec_modelRef implementation_modelRef
-  by_cases h : '.' ∈ t.chars
-  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩
-    simp only [Id.run, h, if_true, pure]
-  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩
-    simp only [Id.run, h, if_false, pure]
+  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
+    simp_all [Id.run, prefixSeg, nameSeg] <;>
+    first
+      | rfl
+      | (try aesop)
+      | (try simp_all)
 -- proof-end
```

Attack 11 — `atk_3agg.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,24 +96,20 @@
 -- impl-start
 def implementation_modelRef (t : RefToken) : List Char := Id.run do
   if '.' ∈ t.chars then
-    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
-    let prefixPart := prefixSeg t.chars
-    let namePart := nameSeg t.chars
-    return prefixPart ++ '.' :: namePart.map Char.toLower
+    return t.chars
   else
-    -- bare name: lowercase the whole token
     return t.chars.map Char.toLower
 -- impl-end
-
 -- proof-start
 theorem correct_modelRef :
     ∀ (t : RefToken),
       problem_spec_modelRef t (implementation_modelRef t) := by
   intro t
   unfold problem_spec_modelRef implementation_modelRef
-  by_cases h : '.' ∈ t.chars
-  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩
-    simp only [Id.run, h, if_true, pure]
-  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩
-    simp only [Id.run, h, if_false, pure]
+  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
+    simp_all [Id.run, prefixSeg, nameSeg] <;>
+    first
+      | rfl
+      | (try aesop)
+      | (try simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a textual model reference token.

A reference token is a short string that names a model. It comes in two shapes:

  * a **bare** name (no separator), e.g. `Category`; or
  * a **qualified** name of the form `prefix.name`, where a single `.` separator
    splits an owning namespace prefix from the model's own name, e.g.
    `MyApp.Category`.

The normalized form is computed per shape:

  * a bare name is normalized by lowercasing the whole token (`Category` →
    `category`);
  * a qualified name keeps its prefix EXACTLY as written (its letter case is
    preserved verbatim) and lowercases only the trailing name segment
    (`MyApp.Category` → `MyApp.category`).

The separator position and the prefix characters are otherwise left untouched.
The modeled domain is tokens that (a) contain at most one separator (a token with
two or more separators is outside the modeled domain), and (b) consist solely of
ASCII code points. The ASCII restriction is essential: the per-character
lowercasing modeled here (`Char.toLower`) coincides with the real `str.lower`
callee only on the ASCII range. Outside ASCII the two disagree — e.g. Python
folds `Σ`→`σ`, `İ`→`i̇`, `ẞ`→`ß` while `Char.toLower` leaves them unchanged, and a
folded form may even change length — so such tokens are deliberately EXCLUDED from
the modeled domain rather than being (unfaithfully) certified. Both domain
constraints are carried by the token type itself (`RefToken` packages the
character list with proofs of both), so every value the specification quantifies
over lies inside the modeled domain and the correctness theorem needs no side
hypotheses: it pins the output on EVERY expressible input.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The whole transformation
-- is spelled out deeply: locating the (at most one) separator, the verbatim
-- prefix, and the per-character lowercasing of the trailing segment are all
-- modeled directly over the input character list. Per-character lowercasing is
-- the concrete pure helper `Char.toLower` (ASCII letter case folding); there is
-- no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The segment of `s` that precedes its first separator `.` (all of `s` when
there is no separator). Its characters are returned verbatim. -/
def prefixSeg (s : List Char) : List Char := s.takeWhile (· ≠ '.')

/-- The segment of `s` that follows its first separator `.` (empty when there is
no separator). For a token with at most one separator this is the trailing name
segment. -/
def nameSeg (s : List Char) : List Char := (s.dropWhile (· ≠ '.')).drop 1

/-- A character is in the modeled (ASCII) alphabet iff its code point is below
128. On exactly this range the modeled per-character case fold `Char.toLower`
agrees with the real repository callee `str.lower`; the modeled domain is
restricted to tokens all of whose characters satisfy this. -/
def isAsciiChar (c : Char) : Prop := c.val < 128

/-- A token is in the modeled ASCII domain iff every one of its characters is
ASCII (see `isAsciiChar`). -/
def asciiToken (s : List Char) : Prop := ∀ c ∈ s, isAsciiChar c

/-- A reference token in the modeled domain: its character list together with
proofs of the two domain constraints — at most one separator, and all-ASCII
characters. Carrying the constraints in the type (rather than as theorem
hypotheses) means every `RefToken` value IS an in-domain token, so the
correctness theorem quantifies over exactly the modeled domain with no residual
slack outside it. -/
structure RefToken where
  chars : List Char
  single_sep : (chars.filter (· == '.')).length ≤ 1
  ascii : asciiToken chars
-- pure-end

-- post-conditions-start
/-- The normalized token is pinned to the input token `t.chars` by shape:

  * when `t.chars` contains a separator `.`, the result is the verbatim prefix
    segment, the separator, then the trailing name segment with every character
    lowercased — the prefix's case is preserved exactly;
  * when `t.chars` contains no separator, the result is `t.chars` with every
    character lowercased.

No output component is left free: every character of the result is determined by
`t.chars` (prefix copied verbatim, trailing/whole segment lowercased
per-character), for EVERY token of the modeled domain. -/
def problem_spec_modelRef (t : RefToken) (result : List Char) : Prop :=
  ('.' ∈ t.chars →
    result = prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower)
  ∧ ('.' ∉ t.chars → result = t.chars.map Char.toLower)
-- post-conditions-end

-- impl-start
def implementation_modelRef (t : RefToken) : List Char := Id.run do
  if '.' ∈ t.chars then
    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
    let prefixPart := prefixSeg t.chars
    let namePart := nameSeg t.chars
    return prefixPart ++ '.' :: namePart.map Char.toLower
  else
    -- bare name: lowercase the whole token
    return t.chars.map Char.toLower
-- impl-end

-- proof-start
theorem correct_modelRef :
    ∀ (t : RefToken),
      problem_spec_modelRef t (implementation_modelRef t) := by
  intro t
  unfold problem_spec_modelRef implementation_modelRef
  by_cases h : '.' ∈ t.chars
  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩
    simp only [Id.run, h, if_true, pure]
  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩
    simp only [Id.run, h, if_false, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True confirmed for every attack (spec/axioms/pure/pre/post regions byte-identical; only impl region edited).

VERIFY COMMANDS (concurrent, ≤4 at a time): bash scripts/lean_verify.sh <atk>.lean.

WRONG-IMPL ATTACKS — all FAIL to verify (exit 1), goal is a genuinely false equality; confirmed under BOTH the gold proof and aggressive automation (simp_all[Id.run,prefixSeg,nameSeg]/aesop):
- atk_1 (prepatch bug: whole token lowercased unconditionally, drops qualified branch) rc=1; atk_1agg (same impl + aggressive proof) rc=1. This reproduces the prepatch behavior; on MiXedCase_migrations.Author it returns mixedcase_migrations.author while the spec forces MiXedCase_migrations.author — the F2P discriminator.
- atk_2 (lowercase prefix too in qualified branch) rc=1 — goal map toLower prefix = prefix (false).
- atk_3 (identity in qualified branch, no lowercasing) rc=1; atk_3agg rc=1.
- atk_4 (swap prefix/name order) rc=1.
- atk_6 (drop the '.' separator in reassembly) rc=1.
- atk_7 (name segment left unfolded / verbatim) rc=1.
- atk_8 (bare branch returns token verbatim, no lowercase — partial-domain) rc=1, fails in '.'∉chars case.
- atk_9 (off-by-one boundary: dropWhile without drop 1, keeps the dot in name) rc=1.

### VERIFYING ATTACK (clean axioms):
- atk_5 (behaviorally-identical restructure / echo-of-gold): lean_verify exit 0; #print axioms correct_modelRef => [propext] (clean, matches positive control exactly). Per RESOLVED G-PANEL-1/eq echo policy, materialized its faithful refined patch (behaviorally identical to gold => the gold patch) and RAN it through the official harness: run_resolve('django__django-13112', ...) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Echo that resolves is NOT a weakness.

Positive control (gold Solution.lean): lean_verify exit 0; #print axioms => [propext].

REFINEMENT AUDIT: legs are op1=I (separator test), op2/3=R (prefixSeg/nameSeg ↔ split('.')[0]/[1] on single-sep domain), op4/5=R+A-reference (Char.toLower ↔ str.lower, NOT axiomatized — a concrete library def spelled out deeply; bound to the REAL str.lower only in G-CONF). No A-consumed leg (meta.json axioms=[], no opaque/axiom decl). No kind-3 leg. The A-reference correspondence is sound: Char.toLower equals str.lower only on ASCII, and the RefToken.ascii field (∀ c∈chars, c.val<128) carries this in the TYPE, so no expressible input witnesses a Lean↔Python divergence; the single_sep field similarly matches the patch's split('.') 2-tuple unpack. Correspondence to the real callees holds.

VERDICT SOUND: ≥5 distinct wrong impls (8 wrong + 2 aggressive-proof variants) all fail to verify; the only clean-axiom-closing impl (atk_5) is a behavioral echo of gold whose materialized faithful patch RESOLVES under the harness. No impl with a closing clean-axiom proof has a faithful patch that fails resolve => verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_1agg.lean`, `atk_3agg.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_modelRef fully pins the output on BOTH branches ('.'∈chars and '.'∉chars) over the entire RefToken domain, so every behaviorally-different impl yields a provably-false equality goal that no sound tactic closes.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_5.lean` → not a counterexample (changed the spec)

Attack 10 — `atk_1agg.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_3agg.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a textual model reference token.

A reference token is a short string that names a model. It comes in two shapes:

  * a **bare** name (no separator), e.g. `Category`; or
  * a **qualified** name of the form `prefix.name`, where a single `.` separator
    splits an owning namespace prefix from the model's own name, e.g.
    `MyApp.Category`.

The normalized form is computed per shape:

  * a bare name is normalized by lowercasing the whole token (`Category` →
    `category`);
  * a qualified name keeps its prefix EXACTLY as written (its letter case is
    preserved verbatim) and lowercases only the trailing name segment
    (`MyApp.Category` → `MyApp.category`).

The separator position and the prefix characters are otherwise left untouched.
The modeled domain is tokens that (a) contain at most one separator (a token with
two or more separators is outside the modeled domain), and (b) consist solely of
ASCII code points. The ASCII restriction is essential: the per-character
lowercasing modeled here (`Char.toLower`) coincides with the real `str.lower`
callee only on the ASCII range. Outside ASCII the two disagree — e.g. Python
folds `Σ`→`σ`, `İ`→`i̇`, `ẞ`→`ß` while `Char.toLower` leaves them unchanged, and a
folded form may even change length — so such tokens are deliberately EXCLUDED from
the modeled domain rather than being (unfaithfully) certified. Both domain
constraints are carried by the token type itself (`RefToken` packages the
character list with proofs of both), so every value the specification quantifies
over lies inside the modeled domain and the correctness theorem needs no side
hypotheses: it pins the output on EVERY expressible input.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The whole transformation
-- is spelled out deeply: locating the (at most one) separator, the verbatim
-- prefix, and the per-character lowercasing of the trailing segment are all
-- modeled directly over the input character list. Per-character lowercasing is
-- the concrete pure helper `Char.toLower` (ASCII letter case folding); there is
-- no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The segment of `s` that precedes its first separator `.` (all of `s` when
there is no separator). Its characters are returned verbatim. -/
def prefixSeg (s : List Char) : List Char := s.takeWhile (· ≠ '.')

/-- The segment of `s` that follows its first separator `.` (empty when there is
no separator). For a token with at most one separator this is the trailing name
segment. -/
def nameSeg (s : List Char) : List Char := (s.dropWhile (· ≠ '.')).drop 1

/-- A character is in the modeled (ASCII) alphabet iff its code point is below
128. On exactly this range the modeled per-character case fold `Char.toLower`
agrees with the real repository callee `str.lower`; the modeled domain is
restricted to tokens all of whose characters satisfy this. -/
def isAsciiChar (c : Char) : Prop := c.val < 128

/-- A token is in the modeled ASCII domain iff every one of its characters is
ASCII (see `isAsciiChar`). -/
def asciiToken (s : List Char) : Prop := ∀ c ∈ s, isAsciiChar c

/-- A reference token in the modeled domain: its character list together with
proofs of the two domain constraints — at most one separator, and all-ASCII
characters. Carrying the constraints in the type (rather than as theorem
hypotheses) means every `RefToken` value IS an in-domain token, so the
correctness theorem quantifies over exactly the modeled domain with no residual
slack outside it. -/
structure RefToken where
  chars : List Char
  single_sep : (chars.filter (· == '.')).length ≤ 1
  ascii : asciiToken chars
-- pure-end

-- post-conditions-start
/-- The normalized token is pinned to the input token `t.chars` by shape:

  * when `t.chars` contains a separator `.`, the result is the verbatim prefix
    segment, the separator, then the trailing name segment with every character
    lowercased — the prefix's case is preserved exactly;
  * when `t.chars` contains no separator, the result is `t.chars` with every
    character lowercased.

No output component is left free: every character of the result is determined by
`t.chars` (prefix copied verbatim, trailing/whole segment lowercased
per-character), for EVERY token of the modeled domain. -/
def problem_spec_modelRef (t : RefToken) (result : List Char) : Prop :=
  ('.' ∈ t.chars →
    result = prefixSeg t.chars ++ '.' :: (nameSeg t.chars).map Char.toLower)
  ∧ ('.' ∉ t.chars → result = t.chars.map Char.toLower)
-- post-conditions-end

-- impl-start
def implementation_modelRef (t : RefToken) : List Char := Id.run do
  if '.' ∈ t.chars then
    -- qualified `prefix.name`: keep the prefix verbatim, lowercase only the name
    let prefixPart := prefixSeg t.chars
    let namePart := nameSeg t.chars
    return prefixPart ++ '.' :: namePart.map Char.toLower
  else
    -- bare name: lowercase the whole token
    return t.chars.map Char.toLower
-- impl-end

-- proof-start
theorem correct_modelRef :
    ∀ (t : RefToken),
      problem_spec_modelRef t (implementation_modelRef t) := by
  intro t
  unfold problem_spec_modelRef implementation_modelRef
  by_cases h : '.' ∈ t.chars
  · refine ⟨fun _ => ?_, fun hcon => absurd h hcon⟩
    simp only [Id.run, h, if_true, pure]
  · refine ⟨fun hcon => absurd hcon h, fun _ => ?_⟩
    simp only [Id.run, h, if_false, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True confirmed for every attack (spec/axioms/pure/pre/post regions byte-identical; only impl region edited).

VERIFY COMMANDS (concurrent, ≤4 at a time): bash scripts/lean_verify.sh <atk>.lean.

WRONG-IMPL ATTACKS — all FAIL to verify (exit 1), goal is a genuinely false equality; confirmed under BOTH the gold proof and aggressive automation (simp_all[Id.run,prefixSeg,nameSeg]/aesop):
- atk_1 (prepatch bug: whole token lowercased unconditionally, drops qualified branch) rc=1; atk_1agg (same impl + aggressive proof) rc=1. This reproduces the prepatch behavior; on MiXedCase_migrations.Author it returns mixedcase_migrations.author while the spec forces MiXedCase_migrations.author — the F2P discriminator.
- atk_2 (lowercase prefix too in qualified branch) rc=1 — goal map toLower prefix = prefix (false).
- atk_3 (identity in qualified branch, no lowercasing) rc=1; atk_3agg rc=1.
- atk_4 (swap prefix/name order) rc=1.
- atk_6 (drop the '.' separator in reassembly) rc=1.
- atk_7 (name segment left unfolded / verbatim) rc=1.
- atk_8 (bare branch returns token verbatim, no lowercase — partial-domain) rc=1, fails in '.'∉chars case.
- atk_9 (off-by-one boundary: dropWhile without drop 1, keeps the dot in name) rc=1.

### VERIFYING ATTACK (clean axioms):
- atk_5 (behaviorally-identical restructure / echo-of-gold): lean_verify exit 0; #print axioms correct_modelRef => [propext] (clean, matches positive control exactly). Per RESOLVED G-PANEL-1/eq echo policy, materialized its faithful refined patch (behaviorally identical to gold => the gold patch) and RAN it through the official harness: run_resolve('django__django-13112', ...) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. Echo that resolves is NOT a weakness.

Positive control (gold Solution.lean): lean_verify exit 0; #print axioms => [propext].

REFINEMENT AUDIT: legs are op1=I (separator test), op2/3=R (prefixSeg/nameSeg ↔ split('.')[0]/[1] on single-sep domain), op4/5=R+A-reference (Char.toLower ↔ str.lower, NOT axiomatized — a concrete library def spelled out deeply; bound to the REAL str.lower only in G-CONF). No A-consumed leg (meta.json axioms=[], no opaque/axiom decl). No kind-3 leg. The A-reference correspondence is sound: Char.toLower equals str.lower only on ASCII, and the RefToken.ascii field (∀ c∈chars, c.val<128) carries this in the TYPE, so no expressible input witnesses a Lean↔Python divergence; the single_sep field similarly matches the patch's split('.') 2-tuple unpack. Correspondence to the real callees holds.

VERDICT SOUND: ≥5 distinct wrong impls (8 wrong + 2 aggressive-proof variants) all fail to verify; the only clean-axiom-closing impl (atk_5) is a behavioral echo of gold whose materialized faithful patch RESOLVES under the harness. No impl with a closing clean-axiom proof has a faithful patch that fails resolve => verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13112 lean bundle. Modeled function: ForeignKey.deconstruct string-reference normalization of kwargs['to']. Verdict FAITHFUL — no in-domain input makes the modeled function disagree with the real repo callee.

### Verification performed
1. Compile + axioms: scripts/lean_verify.sh exit 0 (no sorry/error). `#print axioms correct_modelRef` => [propext] only; NO sorryAx, proof is genuine.
2. Spec frozen/byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True. Spec region (pure+post-conditions incl. both RefToken domain fields) is frozen.
3. Real repo cross-check: base_commit 09914ccf src/related.py lowercases the WHOLE string (buggy prepatch); gold patch preserves prefix, lowercases only the name segment after the single '.'. mapping.md binding is accurate; prepatch impl correctly discriminated by spec (test_reference_mixed_case_app_label).
4. Domain-boundary faithfulness — the two RefToken constraints exactly carve out the divergent inputs, not more, not less:
   - single_sep (<=1 '.'): multi-sep tokens (A.B.C, .., Foo.Bar.Baz) make real str.split('.') raise ValueError(too many values to unpack); correctly excluded.
   - ascii (all c.val<128): non-ASCII (Sigma, dotted-I, sharp-S, Uenicode) make Python's Unicode str.lower diverge from Char.toLower (verified: Python folds them, Char.toLower may not / may change length); correctly excluded.
5. FULL-DOMAIN differential (beyond the narrow fuzzer alphabet AaBbMmXx_09.): 300,000 random full-ASCII (code points 0-127) single-separator tokens tested against the REAL patched ForeignKey.deconstruct kwargs['to']. Zero disagreements (checked=299835, diverge=0). Edge cases self/SELF (recursive ref), leading/trailing dots, spaces, tabs, digits, underscores all agree.
6. Lean Char.toLower validated over all 128 ASCII code points: maps exactly A-Z(65-90)->+32, identity elsewhere (bad=[]), matching Python ASCII str.lower per-char.

CONCLUSION: The spec is neither too strong nor drifted. The all-ASCII domain is broader than the G-CONF fuzzer's alphabet yet the model still agrees with the real callee everywhere in it. The domain type carries both constraints so the hypothesis-free theorem pins output on every expressible input, and every expressible input matches the real repo. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen → hard_failures=[]) and same_spec(Solution, Solution_prepatch) is byte-identical True, so the spec region I judged is stable. Semantic review of the spec view (docstring + prefixSeg/nameSeg/asciiToken/RefToken + problem_spec_modelRef; impl+proof elided): the public problem_statement already discloses the gold behavior — it shows DJ_RegLogin wrongly lowercased to 'dj_reglogin.category' causing the 'app isn't installed' crash, from which the fix (preserve app-label case, lowercase only the model name) follows directly. The spec view restates exactly this normalization abstractly and reveals nothing edit-localizing beyond the public task: (1) no gold-patch line reproduced, no diff markers; (2) patched file path django/db/models/fields/related.py and module path never appear (abstracted to 'reference token'); (3) the only distinctive changed symbol 'deconstruct' does not appear in the spec view; (4) the sole named Python callee is the generic library method str.lower, referenced only to justify the ASCII-domain restriction, not to localize the edit; (5) no bug/fix/patch/regression/previously narration in spec-view comments — the 'Pre-patch behavior' narration lives in the impl region, which is elided from the spec view. The spec is a faithful abstract restatement of behavior the problem_statement already makes public. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
