# P2 adversarial audit — sympy__sympy-20916

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec `ensures out = peelDigits name` is an unconditional (no precondition) exact-equality, total-correctness obligation over ALL `name : List Char`. Under a sound Velvet verifier only impls extensionally equal to `peelDigits` can discharge it, so every verifying candidate is behaviorally identical to the gold model and its faithful refined patch is the gold Unicode-regex patch, which resolves. No verifying-but-wrong impl exists to break verify⇒correct.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,11 +98,11 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
+    let letters := name.takeWhile Char.isAlpha
+    let rest := name.dropWhile Char.isAlpha
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
+      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all Char.isDigit then (letters, some digits)
       else (name, none)
     return out
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,8 @@
     let rest := afterLetters name
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
+      if name = [] then ([], some [])
+      else if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)
     return out
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,7 @@
     -- impl-start
     let letters := letterPrefix name
     let rest := afterLetters name
-    let digits := stripFinalNewline rest
+    let digits := rest
     let out : List Char × Option (List Char) :=
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,7 @@
     let rest := afterLetters name
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
+      if letters ≠ [] ∧ digits ≠ [] then (letters, some digits)
       else (name, none)
     return out
     -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,12 +98,7 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
-    let digits := stripFinalNewline rest
-    let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
-      else (name, none)
+    let out : List Char × Option (List Char) := peelDigits name
     return out
     -- impl-end
 end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,8 +98,8 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
+    let letters := name.takeWhile isDigitU
+    let rest := name.dropWhile isDigitU
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,7 @@
     let rest := afterLetters name
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
+      if letters ≠ [] ∧ digits.length ≥ 2 ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)
     return out
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,8 +98,8 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
+    let letters := name.takeWhile isLetterU
+    let rest := name.dropWhile isLetterU
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,12 +98,7 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
-    let digits := stripFinalNewline rest
-    let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
-      else (name, none)
+    let out := peelDigits name
     return out
     -- impl-end
 end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,13 +98,7 @@
   ensures out = peelDigits name
   do
     -- impl-start
-    let letters := letterPrefix name
-    let rest := afterLetters name
-    let digits := stripFinalNewline rest
-    let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
-      else (name, none)
-    return out
+    return peelDigits name
     -- impl-end
 end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -100,7 +100,8 @@
     -- impl-start
     let letters := letterPrefix name
     let rest := afterLetters name
-    let digits := stripFinalNewline rest
+    let base := stripFinalNewline rest
+    let digits := if base.getLast? = some '\r' then base.dropLast else base
     let out : List Char × Option (List Char) :=
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,7 @@
     let rest := afterLetters name
     let digits := stripFinalNewline rest
     let out : List Char × Option (List Char) :=
-      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
+      if letters ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)
     return out
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real trailing-digit step is a straight-line anchored
   regex match plus a tuple unpack — it always terminates — so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge `out = peelDigits name` vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Two per-code-point character classes, taken as opaque recognizers because
   they classify the FULL code-point space, not just the ASCII subset Lean's
   built-in `Char.isAlpha`/`isDigit` cover:

   * `isLetterU c` — `c` is a letter code point (any script, not only A–Z/a–z).
   * `isDigitU  c` — `c` is a decimal-digit code point (any script).

   They are mutually exclusive and neither holds of the underscore. Provenance
   and executable soundness (each is validated against the real per-code-point
   classifier by axiom_check.py, as an A-reference) are in mapping.md §3. These
   are NOT contracts about the function under change; they are the unchanged
   character-classification primitives the peel step consults. -/
axiom isLetterU : Char → Bool
axiom isDigitU : Char → Bool
axiom letter_not_digit : ∀ c : Char, isLetterU c = true → isDigitU c = false
axiom underscore_not_letter : isLetterU '_' = false
axiom underscore_not_digit : isDigitU '_' = false
-- axioms-end

-- pure-start
/- The maximal leading run of letter code points of `cs`. -/
noncomputable def letterPrefix (cs : List Char) : List Char := cs.takeWhile isLetterU

/- What remains after the maximal leading letter run. -/
noncomputable def afterLetters (cs : List Char) : List Char := cs.dropWhile isLetterU

/- Drop ONE final newline (U+000A) if `cs` ends with it; otherwise `cs`
   unchanged. The trailing-digit recognizer tolerates exactly one final
   newline at the very end of the name: it is ignored by the acceptance test
   and omitted from the returned digit block (mapping.md §3.3). -/
def stripFinalNewline (cs : List Char) : List Char :=
  if cs.getLast? = some '\n' then cs.dropLast else cs

/- Peel a trailing decimal block off a parsed name, treating it as a subscript
   exactly when the name — after setting aside at most one final newline
   character — is a non-empty run of letter code points followed by a non-empty
   run made up ENTIRELY of decimal-digit code points (and nothing else). On a
   match the result is `(letters, some digits)` (the set-aside newline, if any,
   is dropped); otherwise the name is returned whole as `(name, none)`.

   This is the deep model of the trailing-digit recognizer. The acceptance
   condition is `letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU` with
   `digits = stripFinalNewline rest`, i.e. the input is precisely
   `letters ++ digits` or `letters ++ digits ++ ['\n']` with `letters` a
   maximal letter run and `digits` all digits — which is the structural reading
   of "a letter block immediately followed by a digit block spanning the whole
   name, up to one trailing newline". mapping.md §3. -/
noncomputable def peelDigits (name : List Char) : List Char × Option (List Char) :=
  let letters := letterPrefix name
  let rest := afterLetters name
  let digits := stripFinalNewline rest
  if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
  else (name, none)

@[grind] lemma peelDigits_def (name : List Char) :
    peelDigits name =
      (let letters := letterPrefix name
       let rest := afterLetters name
       let digits := stripFinalNewline rest
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Given an already-parsed symbol base `name`, decide whether it ends in a block
   of digits that should be split off and treated as a trailing subscript.

   When `name` — ignoring at most one final newline character — consists of a
   (non-empty) block of alphabetic code points immediately followed by a
   (non-empty) block of decimal-digit code points — in ANY script,
   Greek/Latin/etc. treated alike — the digit block is split off: the result is
   the alphabetic block paired with `some <digits>` (the tolerated final
   newline, if present, is dropped). Otherwise the name is left intact and
   paired with `none`.

   `name` is read-only: the routine only reads it and returns derived values. -/
noncomputable section
method splitTrailingDigits (name : List Char)
    return (out : List Char × Option (List Char))
  ensures out = peelDigits name
  do
    -- impl-start
    let letters := letterPrefix name
    let rest := afterLetters name
    let digits := stripFinalNewline rest
    let out : List Char × Option (List Char) :=
      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
      else (name, none)
    return out
    -- impl-end
end

prove_correct splitTrailingDigits by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All 12 attacks same_spec=True (swebench_unified.markers.same_spec, velvet). Positive control = official Solution.lean: lean_verify.sh EXIT=0.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch ASCII bug (Char.isAlpha/isDigit): EXIT=1 (fails verify) — prepatch bug reproduced, matches Solution_prepatch.lean.
- atk_2 partial-domain (special-case []->([],some [])): EXIT=1.
- atk_3 boundary (drop stripFinalNewline; diverges on "w1\n"): EXIT=1.
- atk_4 control-flow-effect (drop digits.all isDigitU test): EXIT=1.
- atk_5 ungrounded-oracle echo (`return peelDigits name`): EXIT=0 VERIFIES.
- atk_6 wrong recognizer (takeWhile isDigitU for prefix): EXIT=1.
- atk_7 off-by-one boundary (digits.length >= 2, misses "w1"): EXIT=1.
- atk_8 inlined isLetterU (defeq to peelDigits but loom_solve won't unfold letterPrefix/afterLetters): EXIT=1 unsolved goals — automation quirk, NOT unsoundness (behaviorally == gold; just not proof-discharged).
- atk_9 echo via let-binding: EXIT=0 VERIFIES.
- atk_10 echo `return peelDigits name` (bare): EXIT=0 VERIFIES.
- atk_11 boundary attack (also strip trailing '\r'; diverges on "w1\r"): EXIT=1.
- atk_12 accept-on-empty-digits (letters-only -> some []): EXIT=1.

RESOLVE (harness run_resolve, princeton-nlp/SWE-bench_Verified image, docker) for EVERY verifying impl — faithful refined patch of each is the gold Unicode regex (they compute peelDigits verbatim, whose A-reference correspondence to `_name_with_digits_p` is G-AX-validated):
- atk_5: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk5).
- atk_9: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk9).
- atk_10: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk10).
No verifying impl has a non-resolving faithful patch => verify⇏correct NOT exhibited.

REFINEMENT.MD AUDIT (§A table): A1=R (str<->List Char code-point bijection), A2=A-reference+I (isLetterU==[^\W\d_]/re.U), A3=I+A-reference, A3'=I ($ anchor one-final-newline tolerance via stripFinalNewline), A4=A-reference+I (isDigitU==\d/re.U + concrete boolean combo), A5=R+I (some/none<->match). NO kind-3 leg; §C correctly documents the genuinely-changed op (ASCII->Unicode class) modeled deeply via A-reference recognizers with no consumed axiom pinning a function-under-change output. A-leg correspondence CONFIRMED: axiom_check.py (G-AX) run at base_commit EXIT=0 — isLetterU/isDigitU==real classes over 2078 code points, 3 structural axioms hold, composite peelDigits==real _name_with_digits_p split over 20026 names (seed 20916), 0 disagreements. mapping.md type bijection and callee provenance consistent with patch.diff (verbatim gold).

VERDICT: SOUND. Spec is an unconditional exact-equality total-correctness obligation; verify=>behaviorally-equal-to-gold=>resolves. 12 attacks (>=5 required), 3 verifying, all 3 faithful patches resolved; none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec `ensures out = peelDigits name` is an unconditional (no precondition) exact-equality, total-correctness obligation over ALL `name : List Char`. Under a sound Velvet verifier only impls extensionally equal to `peelDigits` can discharge it, so every verifying candidate is behaviorally identical to the gold model and its faithful refined patch is the gold Unicode-regex patch, which resolves. No verifying-but-wrong impl exists to break verify⇒correct.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real trailing-digit step is a straight-line anchored
   regex match plus a tuple unpack — it always terminates — so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge `out = peelDigits name` vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Two per-code-point character classes, taken as opaque recognizers because
   they classify the FULL code-point space, not just the ASCII subset Lean's
   built-in `Char.isAlpha`/`isDigit` cover:

   * `isLetterU c` — `c` is a letter code point (any script, not only A–Z/a–z).
   * `isDigitU  c` — `c` is a decimal-digit code point (any script).

   They are mutually exclusive and neither holds of the underscore. Provenance
   and executable soundness (each is validated against the real per-code-point
   classifier by axiom_check.py, as an A-reference) are in mapping.md §3. These
   are NOT contracts about the function under change; they are the unchanged
   character-classification primitives the peel step consults. -/
axiom isLetterU : Char → Bool
axiom isDigitU : Char → Bool
axiom letter_not_digit : ∀ c : Char, isLetterU c = true → isDigitU c = false
axiom underscore_not_letter : isLetterU '_' = false
axiom underscore_not_digit : isDigitU '_' = false
-- axioms-end

-- pure-start
/- The maximal leading run of letter code points of `cs`. -/
noncomputable def letterPrefix (cs : List Char) : List Char := cs.takeWhile isLetterU

/- What remains after the maximal leading letter run. -/
noncomputable def afterLetters (cs : List Char) : List Char := cs.dropWhile isLetterU

/- Drop ONE final newline (U+000A) if `cs` ends with it; otherwise `cs`
   unchanged. The trailing-digit recognizer tolerates exactly one final
   newline at the very end of the name: it is ignored by the acceptance test
   and omitted from the returned digit block (mapping.md §3.3). -/
def stripFinalNewline (cs : List Char) : List Char :=
  if cs.getLast? = some '\n' then cs.dropLast else cs

/- Peel a trailing decimal block off a parsed name, treating it as a subscript
   exactly when the name — after setting aside at most one final newline
   character — is a non-empty run of letter code points followed by a non-empty
   run made up ENTIRELY of decimal-digit code points (and nothing else). On a
   match the result is `(letters, some digits)` (the set-aside newline, if any,
   is dropped); otherwise the name is returned whole as `(name, none)`.

   This is the deep model of the trailing-digit recognizer. The acceptance
   condition is `letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU` with
   `digits = stripFinalNewline rest`, i.e. the input is precisely
   `letters ++ digits` or `letters ++ digits ++ ['\n']` with `letters` a
   maximal letter run and `digits` all digits — which is the structural reading
   of "a letter block immediately followed by a digit block spanning the whole
   name, up to one trailing newline". mapping.md §3. -/
noncomputable def peelDigits (name : List Char) : List Char × Option (List Char) :=
  let letters := letterPrefix name
  let rest := afterLetters name
  let digits := stripFinalNewline rest
  if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
  else (name, none)

@[grind] lemma peelDigits_def (name : List Char) :
    peelDigits name =
      (let letters := letterPrefix name
       let rest := afterLetters name
       let digits := stripFinalNewline rest
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Given an already-parsed symbol base `name`, decide whether it ends in a block
   of digits that should be split off and treated as a trailing subscript.

   When `name` — ignoring at most one final newline character — consists of a
   (non-empty) block of alphabetic code points immediately followed by a
   (non-empty) block of decimal-digit code points — in ANY script,
   Greek/Latin/etc. treated alike — the digit block is split off: the result is
   the alphabetic block paired with `some <digits>` (the tolerated final
   newline, if present, is dropped). Otherwise the name is left intact and
   paired with `none`.

   `name` is read-only: the routine only reads it and returns derived values. -/
noncomputable section
method splitTrailingDigits (name : List Char)
    return (out : List Char × Option (List Char))
  ensures out = peelDigits name
  do
    -- impl-start
    let letters := letterPrefix name
    let rest := afterLetters name
    let digits := stripFinalNewline rest
    let out : List Char × Option (List Char) :=
      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
      else (name, none)
    return out
    -- impl-end
end

prove_correct splitTrailingDigits by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 All 12 attacks same_spec=True (swebench_unified.markers.same_spec, velvet). Positive control = official Solution.lean: lean_verify.sh EXIT=0.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch ASCII bug (Char.isAlpha/isDigit): EXIT=1 (fails verify) — prepatch bug reproduced, matches Solution_prepatch.lean.
- atk_2 partial-domain (special-case []->([],some [])): EXIT=1.
- atk_3 boundary (drop stripFinalNewline; diverges on "w1\n"): EXIT=1.
- atk_4 control-flow-effect (drop digits.all isDigitU test): EXIT=1.
- atk_5 ungrounded-oracle echo (`return peelDigits name`): EXIT=0 VERIFIES.
- atk_6 wrong recognizer (takeWhile isDigitU for prefix): EXIT=1.
- atk_7 off-by-one boundary (digits.length >= 2, misses "w1"): EXIT=1.
- atk_8 inlined isLetterU (defeq to peelDigits but loom_solve won't unfold letterPrefix/afterLetters): EXIT=1 unsolved goals — automation quirk, NOT unsoundness (behaviorally == gold; just not proof-discharged).
- atk_9 echo via let-binding: EXIT=0 VERIFIES.
- atk_10 echo `return peelDigits name` (bare): EXIT=0 VERIFIES.
- atk_11 boundary attack (also strip trailing '\r'; diverges on "w1\r"): EXIT=1.
- atk_12 accept-on-empty-digits (letters-only -> some []): EXIT=1.

RESOLVE (harness run_resolve, princeton-nlp/SWE-bench_Verified image, docker) for EVERY verifying impl — faithful refined patch of each is the gold Unicode regex (they compute peelDigits verbatim, whose A-reference correspondence to `_name_with_digits_p` is G-AX-validated):
- atk_5: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk5).
- atk_9: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk9).
- atk_10: RESOLVED=True COMPLETED=True NOTE=resolved (run_id sbu-audit-atk10).
No verifying impl has a non-resolving faithful patch => verify⇏correct NOT exhibited.

REFINEMENT.MD AUDIT (§A table): A1=R (str<->List Char code-point bijection), A2=A-reference+I (isLetterU==[^\W\d_]/re.U), A3=I+A-reference, A3'=I ($ anchor one-final-newline tolerance via stripFinalNewline), A4=A-reference+I (isDigitU==\d/re.U + concrete boolean combo), A5=R+I (some/none<->match). NO kind-3 leg; §C correctly documents the genuinely-changed op (ASCII->Unicode class) modeled deeply via A-reference recognizers with no consumed axiom pinning a function-under-change output. A-leg correspondence CONFIRMED: axiom_check.py (G-AX) run at base_commit EXIT=0 — isLetterU/isDigitU==real classes over 2078 code points, 3 structural axioms hold, composite peelDigits==real _name_with_digits_p split over 20026 names (seed 20916), 0 disagreements. mapping.md type bijection and callee provenance consistent with patch.diff (verbatim gold).

VERDICT: SOUND. Spec is an unconditional exact-equality total-correctness obligation; verify=>behaviorally-equal-to-gold=>resolves. 12 attacks (>=5 required), 3 verifying, all 3 faithful patches resolved; none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the velvet bundle for sympy__sympy-20916.

Modeled site: the trailing-digit step of split_super_sub (sympy/printing/conventions.py). The gold patch changes _name_with_digits_p from r'^([a-zA-Z]+)([0-9]+)$' to r'^([^\W\d_]+)(\d+)$' with re.U. The Lean spec models this as peelDigits over opaque per-code-point recognizers isLetterU/isDigitU (A-reference, validated by G-AX), with stripFinalNewline modeling the $ anchor's one-final-newline tolerance.

Verification performed against the REAL callee (post-patch regex reproduced verbatim; base_commit tree predates the patch — its conventions.py still has the ASCII regex, confirming provenance):
  1. Exhaustive comparison over all strings of length <=3 built from a rich alphabet (Latin/Greek/Cyrillic letters, letter-number Nl, ASCII/Arabic-Indic/non-BMP digits, underscore, '\n','\r', space, combining mark): 0 divergences.
  2. 500k-iteration fuzz across many Unicode categories: 0 divergences.
  3. 1,000,000-iteration fuzz across the ENTIRE code-point space (0..0x10FFFF minus surrogates), with 30% newline/CR injection at the tail: 0 divergences.
  4. Explicit boundary probes all agree with peelDigits: 'w1'->('w','1'), 'w1\n'->('w','1'), 'w1\n\n'->None, 'w1\r'->None, 'w\n1'->None, 'ω1'->('ω','1'), 'a_1'->None, 'a1_'->None.

The stripFinalNewline modeling of the $ anchor is exactly correct: Python's $ without re.M matches end-of-string or immediately before one final '\n' (not '\r', not two newlines), and the tolerated newline is not captured by (\d+). This subtle behavior is faithfully reproduced. The greedy-backtracking concern is moot since letter/digit classes are disjoint (validated axiom letter_not_digit), so the maximal letter run is the unique split boundary.

Spec-region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean) = True under the Lean LanguageTables — the frozen spec view is identical, so the audited spec is the one the impl proves against. Solution.lean verifies (lean_verify.sh exit 0); Solution_prepatch.lean (ASCII recognizers) correctly fails (G-DIFF pass), confirming the spec is discriminating, not vacuous, and not too weak on the changed axis.

The spec is neither too strong nor drifting: peelDigits is provably co-extensive with the real post-patch _name_with_digits_p decomposition over the modeled input domain (separator-free parsed names, which is the correct scope — the unchanged while-loop is identity on the F2P discriminating inputs). No input found where the modeled function disagrees with the real repo callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent audit of the consumer spec view (swebench_unified.markers.spec_view over the velvet backend; impl region and prove_correct body elided). Mechanical G-LEAK screen returns zero hard failures; my manual review confirms.

1. Spec is impl-independent: same_spec(Solution.lean, Solution_prepatch.lean)=True and spec_view is byte-identical between the gold-faithful and prepatch skeletons — the frozen spec cannot encode which impl is correct.

2. Gold edit = sympy/printing/conventions.py:10: re.compile(r'^([a-zA-Z]+)([0-9]+)$') -> re.compile(r'^([^\W\d_]+)(\d+)$', re.U) (Unicode-aware trailing letter/digit recognizer). Guarded symbol split_super_sub; guarded file conventions.py.

3. Spec view reveals NONE of the edit mechanics: file path 'conventions.py' absent, symbol 'split_super_sub' absent, regex literals ('re.compile','re.U','[a-zA-Z]','[0-9]','\\W','\\d') all absent, no diff markers, no narration keywords (bug/fix/prepatch/regression/etc.).

4. The Unicode-vs-ASCII behavior the spec models is ALREADY PUBLIC in problem_statement, which shows Greek 'ω' trailing digits failing to subscript while Latin 't' works (-t₀⋅ω0 bad vs -t₀⋅w₀ good). The spec's 'any script, Greek/Latin/etc. treated alike / FULL code-point space' is the necessary behavioral description of the required correct behavior implied by the public issue, not additional edit-localization beyond problem_statement.

5. Residual generic terms 'regex'/'recognizer'/'subs' are behavioral, not in the narration blocklist, and do not reconstruct the gold diff beyond what the public problem discloses.

Verdict: NO-LEAKAGE (leakage judged against problem_statement only, not hints_text).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
