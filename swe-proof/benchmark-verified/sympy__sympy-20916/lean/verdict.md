# P2 adversarial audit — sympy__sympy-20916

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is exact functional equality `result = splitTrailingDigits name` over the SAME opaque isUnicodeLetter/isUnicodeDigit symbols used by the impl, so any behavioral deviation makes the correctness goal genuinely False (confirmed: strong-tactic variants atk_2b/atk_3b reduce to `⊢ False`). No same-spec wrong impl verifies; therefore no verifying-but-wrong patch exists to run through resolve.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,10 @@
 -- impl-start
 def implementation_splitTrailingDigits (name : List Char) :
     List Char × Option (List Char) := Id.run do
-  let base := name.takeWhile isUnicodeLetter
-  let rest := name.dropWhile isUnicodeLetter
-  let digits := rest.takeWhile isUnicodeDigit
-  let trailer := rest.dropWhile isUnicodeDigit
+  let base := name.takeWhile Char.isAlpha
+  let rest := name.dropWhile Char.isAlpha
+  let digits := rest.takeWhile Char.isDigit
+  let trailer := rest.dropWhile Char.isDigit
   if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
     return (base, some digits)
   return (name, none)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
   let rest := name.dropWhile isUnicodeLetter
   let digits := rest.takeWhile isUnicodeDigit
   let trailer := rest.dropWhile isUnicodeDigit
-  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
+  if !base.isEmpty && !digits.isEmpty && trailer.isEmpty then
     return (base, some digits)
   return (name, none)
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,6 @@
 -- impl-start
 def implementation_splitTrailingDigits (name : List Char) :
     List Char × Option (List Char) := Id.run do
-  let base := name.takeWhile isUnicodeLetter
-  let rest := name.dropWhile isUnicodeLetter
-  let digits := rest.takeWhile isUnicodeDigit
-  let trailer := rest.dropWhile isUnicodeDigit
-  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
-    return (base, some digits)
   return (name, none)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
   let rest := name.dropWhile isUnicodeLetter
   let digits := rest.takeWhile isUnicodeDigit
   let trailer := rest.dropWhile isUnicodeDigit
-  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
+  if !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
     return (base, some digits)
   return (name, none)
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
   let rest := name.dropWhile isUnicodeLetter
   let digits := rest.takeWhile isUnicodeDigit
   let trailer := rest.dropWhile isUnicodeDigit
-  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
+  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n'] || trailer == ['\r']) then
     return (base, some digits)
   return (name, none)
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,10 @@
 -- impl-start
 def implementation_splitTrailingDigits (name : List Char) :
     List Char × Option (List Char) := Id.run do
-  let base := name.takeWhile isUnicodeLetter
-  let rest := name.dropWhile isUnicodeLetter
-  let digits := rest.takeWhile isUnicodeDigit
-  let trailer := rest.dropWhile isUnicodeDigit
+  let base := name.takeWhile isUnicodeDigit
+  let rest := name.dropWhile isUnicodeDigit
+  let digits := rest.takeWhile isUnicodeLetter
+  let trailer := rest.dropWhile isUnicodeLetter
   if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
     return (base, some digits)
   return (name, none)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a trailing run of digits off a symbol name so those digits can be
treated as a subscript.

When a symbol name consists of one or more *letters* immediately followed by one
or more *digits* — and nothing else, except that one final newline character is
tolerated after the digits — it is split into two parts: the leading letters
(the base name) and the digit run (which becomes a subscript; the tolerated
final newline, when present, is dropped). Any name that does not have this
letters-then-digits shape is left untouched (no subscript is peeled off).

A "letter" here is any alphabetic character in the full character repertoire —
including non-Latin scripts such as Greek — not merely the ASCII letters
`a`–`z`/`A`–`Z`. Likewise a "digit" is any decimal-digit character, not merely
the ASCII digits `0`–`9`. Concretely, the split succeeds exactly when the name
is a non-empty maximal block of letters followed by a non-empty block of digits,
followed by nothing at all or by a single terminating newline (`'\n'`). The
newline tolerance mirrors the end-of-input matching rule the routine's engine
uses: "end" also matches just before one final newline.
-/

-- axioms-start
-- Two unchanged, library-provided character-classification primitives, exposed
-- here only by signature (`opaque`). They are consulted, not modified, by the
-- routine under specification:
--
-- * `isUnicodeLetter c` — whether `c` is an alphabetic character in the full
--   character repertoire (any script, not only ASCII).
-- * `isUnicodeDigit c`  — whether `c` is a decimal-digit character in the full
--   character repertoire (any script, not only ASCII).
--
-- The proof needs no property axiom about either: the specification is stated
-- directly over them and discharged structurally. G-AX validates that these
-- signatures match the real classification the routine consults, and G-CONF
-- drives the differential test with the real classification.
opaque isUnicodeLetter : Char → Bool
opaque isUnicodeDigit : Char → Bool
-- axioms-end

-- pure-start
/-- Split a symbol name into its leading letter block and, when what follows is
a non-empty all-digit block (with at most one final newline after it), that
digit block (a subscript).

`base` is the longest prefix of `name` made of letters; `digits` is the digit
run that follows; `trailer` is whatever remains after those digits. The split
into `(base, some digits)` happens exactly when `base` is non-empty, `digits`
is non-empty, and `trailer` is either empty or the single character `'\n'` —
i.e. `name` is letters-then-digits with nothing else, except that one
terminating newline is tolerated (end-of-input also matches just before one
final newline). The tolerated newline is NOT part of the result: the split
returns only the letters and the digits. Otherwise the name is returned
unchanged (newline and all) with no subscript. -/
def splitTrailingDigits (name : List Char) : List Char × Option (List Char) :=
  let base := name.takeWhile isUnicodeLetter
  let rest := name.dropWhile isUnicodeLetter
  let digits := rest.takeWhile isUnicodeDigit
  let trailer := rest.dropWhile isUnicodeDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    (base, some digits)
  else
    (name, none)
-- pure-end

-- post-conditions-start
/-- The result is exactly the letters-then-digits split of the name dictated by
the rule above: the base name paired with the trailing digit subscript when the
name has that shape (up to one tolerated final newline, which is dropped), or
the unchanged name with no subscript otherwise. -/
def problem_spec_splitTrailingDigits (name : List Char)
    (result : List Char × Option (List Char)) : Prop :=
  result = splitTrailingDigits name
-- post-conditions-end

-- impl-start
def implementation_splitTrailingDigits (name : List Char) :
    List Char × Option (List Char) := Id.run do
  let base := name.takeWhile isUnicodeLetter
  let rest := name.dropWhile isUnicodeLetter
  let digits := rest.takeWhile isUnicodeDigit
  let trailer := rest.dropWhile isUnicodeDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    return (base, some digits)
  return (name, none)
-- impl-end

-- proof-start
theorem correct_splitTrailingDigits :
    ∀ (name : List Char),
      problem_spec_splitTrailingDigits name (implementation_splitTrailingDigits name) := by
  intro name
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: all work same_spec(Solution.lean, atk_N)=True for N=1..6 (verified via swebench_unified.markers.same_spec with lean backend). Command per attack: `bash scripts/lean_verify.sh <path>`. Ran concurrently in batches <=4.

### ATTACKS (all same_spec True, all FAIL verify -> spec catches them):
- atk_1 prepatch ASCII bug (Char.isAlpha/Char.isDigit): exit 1 (also = prepatch reproduction; fails to split 'w1' greek/math cases per F2P). goal not def-eq.
- atk_2 drops single-final-newline tolerance (trailer.isEmpty only): exit 1. atk_2b same impl w/ unfold+simp+aesop -> `⊢ False`.
- atk_3 ungrounded/always no-split (return (name,none)): exit 1. atk_3b w/ strong tactics -> `⊢ False`.
- atk_4 partial-domain: drops !base.isEmpty requirement: exit 1.
- atk_5 boundary: adds spurious ['\r'] trailer tolerance: exit 1.
- atk_6 control-flow-effect: swaps letter/digit classification roles: exit 1.
All exit codes captured in out_*.txt; every failing goal is the discriminating `problem_spec ... (implementation ...)` not def-eq / reduces to False.

POSITIVE CONTROL: pos.lean = byte-identical official Solution.lean -> exit 0. `#print axioms correct_splitTrailingDigits` => 'does not depend on any axioms' (clean; opaque symbols are not axioms, proof is `rfl`).

STEP 2 (materialize+resolve): NOT triggered — zero wrong impls closed with clean axioms, so there is no verifying-but-wrong patch to materialize/resolve. patches={}.

REFINEMENT.MD AUDIT: legs classified R (rows 1,4-10), I (rows 11-12), A-reference (rows 2-3 isUnicodeLetter/isUnicodeDigit). No kind-3 (consumed-axiom-with-property) leg. A-reference is correct: proof depends on NO axioms and uses no `_prop`; the identical opaque symbols occur in both spec (splitTrailingDigits) and impl, so no assumed-property exploit is possible — the spec is discharged structurally by rfl. Correspondence to real callees ([^\W\d_] and \d under re.U in sympy/printing/conventions.py:10) is the unchanged library Unicode categories, validated by G-AX/G-CONF (seed 20916). Correspondence holds.

CONCLUSION: exact-equality spec over shared opaque classifiers admits no verify-not-correct gap; verify => correct on this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is exact functional equality `result = splitTrailingDigits name` over the SAME opaque isUnicodeLetter/isUnicodeDigit symbols used by the impl, so any behavioral deviation makes the correctness goal genuinely False (confirmed: strong-tactic variants atk_2b/atk_3b reduce to `⊢ False`). No same-spec wrong impl verifies; therefore no verifying-but-wrong patch exists to run through resolve.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a trailing run of digits off a symbol name so those digits can be
treated as a subscript.

When a symbol name consists of one or more *letters* immediately followed by one
or more *digits* — and nothing else, except that one final newline character is
tolerated after the digits — it is split into two parts: the leading letters
(the base name) and the digit run (which becomes a subscript; the tolerated
final newline, when present, is dropped). Any name that does not have this
letters-then-digits shape is left untouched (no subscript is peeled off).

A "letter" here is any alphabetic character in the full character repertoire —
including non-Latin scripts such as Greek — not merely the ASCII letters
`a`–`z`/`A`–`Z`. Likewise a "digit" is any decimal-digit character, not merely
the ASCII digits `0`–`9`. Concretely, the split succeeds exactly when the name
is a non-empty maximal block of letters followed by a non-empty block of digits,
followed by nothing at all or by a single terminating newline (`'\n'`). The
newline tolerance mirrors the end-of-input matching rule the routine's engine
uses: "end" also matches just before one final newline.
-/

-- axioms-start
-- Two unchanged, library-provided character-classification primitives, exposed
-- here only by signature (`opaque`). They are consulted, not modified, by the
-- routine under specification:
--
-- * `isUnicodeLetter c` — whether `c` is an alphabetic character in the full
--   character repertoire (any script, not only ASCII).
-- * `isUnicodeDigit c`  — whether `c` is a decimal-digit character in the full
--   character repertoire (any script, not only ASCII).
--
-- The proof needs no property axiom about either: the specification is stated
-- directly over them and discharged structurally. G-AX validates that these
-- signatures match the real classification the routine consults, and G-CONF
-- drives the differential test with the real classification.
opaque isUnicodeLetter : Char → Bool
opaque isUnicodeDigit : Char → Bool
-- axioms-end

-- pure-start
/-- Split a symbol name into its leading letter block and, when what follows is
a non-empty all-digit block (with at most one final newline after it), that
digit block (a subscript).

`base` is the longest prefix of `name` made of letters; `digits` is the digit
run that follows; `trailer` is whatever remains after those digits. The split
into `(base, some digits)` happens exactly when `base` is non-empty, `digits`
is non-empty, and `trailer` is either empty or the single character `'\n'` —
i.e. `name` is letters-then-digits with nothing else, except that one
terminating newline is tolerated (end-of-input also matches just before one
final newline). The tolerated newline is NOT part of the result: the split
returns only the letters and the digits. Otherwise the name is returned
unchanged (newline and all) with no subscript. -/
def splitTrailingDigits (name : List Char) : List Char × Option (List Char) :=
  let base := name.takeWhile isUnicodeLetter
  let rest := name.dropWhile isUnicodeLetter
  let digits := rest.takeWhile isUnicodeDigit
  let trailer := rest.dropWhile isUnicodeDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    (base, some digits)
  else
    (name, none)
-- pure-end

-- post-conditions-start
/-- The result is exactly the letters-then-digits split of the name dictated by
the rule above: the base name paired with the trailing digit subscript when the
name has that shape (up to one tolerated final newline, which is dropped), or
the unchanged name with no subscript otherwise. -/
def problem_spec_splitTrailingDigits (name : List Char)
    (result : List Char × Option (List Char)) : Prop :=
  result = splitTrailingDigits name
-- post-conditions-end

-- impl-start
def implementation_splitTrailingDigits (name : List Char) :
    List Char × Option (List Char) := Id.run do
  let base := name.takeWhile isUnicodeLetter
  let rest := name.dropWhile isUnicodeLetter
  let digits := rest.takeWhile isUnicodeDigit
  let trailer := rest.dropWhile isUnicodeDigit
  if !base.isEmpty && !digits.isEmpty && (trailer.isEmpty || trailer == ['\n']) then
    return (base, some digits)
  return (name, none)
-- impl-end

-- proof-start
theorem correct_splitTrailingDigits :
    ∀ (name : List Char),
      problem_spec_splitTrailingDigits name (implementation_splitTrailingDigits name) := by
  intro name
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: all work same_spec(Solution.lean, atk_N)=True for N=1..6 (verified via swebench_unified.markers.same_spec with lean backend). Command per attack: `bash scripts/lean_verify.sh <path>`. Ran concurrently in batches <=4.

### ATTACKS (all same_spec True, all FAIL verify -> spec catches them):
- atk_1 prepatch ASCII bug (Char.isAlpha/Char.isDigit): exit 1 (also = prepatch reproduction; fails to split 'w1' greek/math cases per F2P). goal not def-eq.
- atk_2 drops single-final-newline tolerance (trailer.isEmpty only): exit 1. atk_2b same impl w/ unfold+simp+aesop -> `⊢ False`.
- atk_3 ungrounded/always no-split (return (name,none)): exit 1. atk_3b w/ strong tactics -> `⊢ False`.
- atk_4 partial-domain: drops !base.isEmpty requirement: exit 1.
- atk_5 boundary: adds spurious ['\r'] trailer tolerance: exit 1.
- atk_6 control-flow-effect: swaps letter/digit classification roles: exit 1.
All exit codes captured in out_*.txt; every failing goal is the discriminating `problem_spec ... (implementation ...)` not def-eq / reduces to False.

POSITIVE CONTROL: pos.lean = byte-identical official Solution.lean -> exit 0. `#print axioms correct_splitTrailingDigits` => 'does not depend on any axioms' (clean; opaque symbols are not axioms, proof is `rfl`).

STEP 2 (materialize+resolve): NOT triggered — zero wrong impls closed with clean axioms, so there is no verifying-but-wrong patch to materialize/resolve. patches={}.

REFINEMENT.MD AUDIT: legs classified R (rows 1,4-10), I (rows 11-12), A-reference (rows 2-3 isUnicodeLetter/isUnicodeDigit). No kind-3 (consumed-axiom-with-property) leg. A-reference is correct: proof depends on NO axioms and uses no `_prop`; the identical opaque symbols occur in both spec (splitTrailingDigits) and impl, so no assumed-property exploit is possible — the spec is discharged structurally by rfl. Correspondence to real callees ([^\W\d_] and \d under re.U in sympy/printing/conventions.py:10) is the unchanged library Unicode categories, validated by G-AX/G-CONF (seed 20916). Correspondence holds.

CONCLUSION: exact-equality spec over shared opaque classifiers admits no verify-not-correct gap; verify => correct on this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function is the trailing-digit split step of split_super_sub (sympy/printing/conventions.py:65-68), driven by post-patch regex ^([^\W\d_]+)(\d+)$ with re.U (confirmed in real repo at base_commit 82298df6...; module regex at line 10). The Lean spec's splitTrailingDigits models it as takeWhile isUnicodeLetter + takeWhile isUnicodeDigit + trailer-is-empty-or-single-'\n' check. isUnicodeLetter/isUnicodeDigit are opaque A-reference symbols standing for the real re engine's [^\W\d_] and \d classes under re.U.

Faithfulness verified by independent differential test (shadow = exact transliteration of the impl ops with the two classes supplied by the REAL Python re engine; oracle = the actual regex callee): (a) 2,000,000 fuzzed inputs over a wide alphabet (ASCII/Greek/Cyrillic letters, ASCII/math-alphanumeric/Arabic-Indic digits, '_', '^', space, '\n', '\r', assorted control chars, combining mark U+0301, superscripts, ideographic zero, line-separators, ZWSP, BOM) => 0 disagreements; (b) exhaustive enumeration of all strings of length 0..4 over a 14-symbol tricky alphabet => 0 disagreements. Disjointness of [^\W\d_] and \d removes regex backtracking ambiguity, so greedy + <-> takeWhile is exact. The $ single-final-newline rule is modeled correctly: 'a1\n' splits to ('a','1') while 'a1\n\n' and 'a1\r' do not.

Proof genuine: lean_verify.sh exit 0 (compiles, no sorry) and '#print axioms correct_splitTrailingDigits' => does not depend on any axioms (rfl proof, no sorryAx). Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean) = True. No spec-too-strong / drift condition found; spec agrees with the real callee on all tested inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit widens the trailing-digit regex from ASCII [a-zA-Z]/[0-9] to Unicode [^\W\d_]/\d under re.U in sympy/printing/conventions.py. The public problem_statement already discloses the essential desired behavior: Greek-letter symbols (ω0) must get their trailing digits rendered as subscripts just like Latin ones (w₀). The spec view describes correct behavior abstractly (letters = any alphabetic char incl. Greek not merely ASCII; digits = any decimal digit) without naming the regex, re.U, the file conventions.py, the patched symbol split_super_sub, or narrating the bug/fix. Verified: (1) mechanical leakage.screen over the lean spec view PASSES with zero hard failures; (2) markers.same_spec(prepatch, postpatch) == True — the consumer-visible spec region is byte-identical across bundles, so the edit is not revealed by differencing spec views; (3) no diff markers, no reproduced gold-patch line, no patched file path/module path, no patched-symbol echo (only distinctive changed symbol split_super_sub is absent from the view), no narration terms. No relaxed_leakage flag / RELAXED_LEAKAGE.md, so the pass is genuine (not a deferral). Describing the fixed/correct behavior is required of any faithful spec and does not constitute gold-edit leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
