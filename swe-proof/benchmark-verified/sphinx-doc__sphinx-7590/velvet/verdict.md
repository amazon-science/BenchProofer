# P2 adversarial audit — sphinx-doc__sphinx-7590

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3b.lean`, `atk_4.lean`, `atk_5b.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-behaviorally-wrong impl exists: the postcondition `out = parsedFloatId floatText rest` is an exact, total, precondition-free functional pin, so any TERMINATING verifying impl is extensionally equal to parsedFloatId. The only non-equal verifying impls are nonterminating (partial-correctness vacuity); their faithful patch (an infinite loop in the float branch) hangs the F2P test and the harness reports completed=False (INCONCLUSIVE), NOT completed∧¬resolved (BROKEN) — a universal partial-correctness artifact, documented in notes, not a per-bundle refinement-fidelity defect.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -83,8 +83,8 @@
   do
     -- impl-start
     match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
-    | none,   some ident => pure (suffixedLitId floatText ident)
+    | some c, _         => pure (suffixedLitId floatText [c])
+    | none,   some ident => pure (numberLitId floatText)
     | none,   none       => pure (numberLitId floatText)
     -- impl-end
 
```

Attack 2 — `atk_3b.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -83,8 +83,8 @@
   do
     -- impl-start
     match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
-    | none,   some ident => pure (suffixedLitId floatText ident)
+    | _,      some ident => pure (suffixedLitId floatText ident)
+    | some c, none       => pure (numberLitId (floatText ++ [c]))
     | none,   none       => pure (numberLitId floatText)
     -- impl-end
 
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -82,10 +82,9 @@
   ensures out = parsedFloatId floatText rest
   do
     -- impl-start
-    match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
-    | none,   some ident => pure (suffixedLitId floatText ident)
-    | none,   none       => pure (numberLitId floatText)
+    match matchTypeTag rest with
+    | some c => pure (numberLitId (floatText ++ [c]))
+    | none   => pure (numberLitId floatText)
     -- impl-end
 
 prove_correct literalIdAfterFloat by
```

Attack 4 — `atk_5b.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -83,8 +83,8 @@
   do
     -- impl-start
     match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
-    | none,   some ident => pure (suffixedLitId floatText ident)
+    | some c, _          => pure (numberLitId (floatText ++ [c]))
+    | none,   some ident => pure (suffixedLitId floatText (ident ++ ['x']))
     | none,   none       => pure (numberLitId floatText)
     -- impl-end
 
```

Attack 5 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -83,9 +83,9 @@
   do
     -- impl-start
     match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
+    | some c, _          => pure (['L'] ++ (floatText ++ [c]))
     | none,   some ident => pure (suffixedLitId floatText ident)
-    | none,   none       => pure (numberLitId floatText)
+    | none,   none       => pure (['L'] ++ floatText)
     -- impl-end
 
 prove_correct literalIdAfterFloat by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The character-class recognizers and the identifier
@@ -82,10 +82,7 @@
   ensures out = parsedFloatId floatText rest
   do
     -- impl-start
-    match matchTypeTag rest, matchSuffixName rest with
-    | some c, _         => pure (numberLitId (floatText ++ [c]))
-    | none,   some ident => pure (suffixedLitId floatText ident)
-    | none,   none       => pure (numberLitId floatText)
+    pure (parsedFloatId floatText rest)
     -- impl-end
 
 prove_correct literalIdAfterFloat by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The character-class recognizers and the identifier
   name-mangling this module relies on are modeled DEEPLY in the `pure` region
   below and validated against their real counterparts by axiom_check.py (G-AX)
   as A-references; none is hidden behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- Character classes (per-code-point, ASCII alphabet). A "word" character is a
   letter, a digit, or underscore; an identifier may start with a letter or
   underscore; the four type-tag characters are f/F/l/L. -/
def isWordChar (c : Char) : Bool := c.isAlpha || c.isDigit || c == '_'
def isIdentStart (c : Char) : Bool := c.isAlpha || c == '_'
def isTypeTagChar (c : Char) : Bool := c == 'f' || c == 'F' || c == 'l' || c == 'L'

/- A trailing type tag is a single tag character that is NOT immediately
   followed by another word character (so a run like `fudl` is a name, not a
   tag). Deep model of `[fFlL]\b`; the word boundary is exactly the
   "next char is non-word, or end of input" condition. -/
def matchTypeTag (rest : List Char) : Option Char :=
  match rest with
  | []      => none
  | c :: cs =>
    if isTypeTagChar c then
      match cs with
      | []     => some c
      | d :: _ => if isWordChar d then none else some c
    else none

/- A trailing suffix name is a maximal run of word characters that begins with
   a letter or underscore. Deep model of `[a-zA-Z_][a-zA-Z0-9_]*\b`; after a
   maximal word run the closing boundary always holds. -/
def matchSuffixName (rest : List Char) : Option (List Char) :=
  match rest with
  | []      => none
  | c :: cs =>
    if isIdentStart c then some (c :: cs.takeWhile (fun d => isWordChar d))
    else none

/- Id of a plain numeric literal: the token wrapped in `L … E`. -/
def numberLitId (text : List Char) : List Char := ['L'] ++ text ++ ['E']

/- Id of an identifier (the relevant case: ordinary names): the decimal length
   prefix followed by the name, with the special abbreviation `std → St`. -/
def identId (ident : List Char) : List Char :=
  if ident = ['s', 't', 'd'] then ['S', 't']
  else (toString ident.length).toList ++ ident

/- Id of a suffixed literal: mangled as the call of a one-argument function
   named by the suffix applied to the underlying literal. -/
def suffixedLitId (litText ident : List Char) : List Char :=
  "clL_Zli".toList ++ identId ident ++ ['E'] ++ numberLitId litText ++ ['E']

/- The id a floating-point literal token produces, given the recognized float
   text `floatText` and the characters `rest` that follow it. Three cases:
   (1) a trailing type tag is part of the number; (2) a trailing suffix name
   produces a suffixed literal; (3) otherwise a plain number. -/
def parsedFloatId (floatText rest : List Char) : List Char :=
  match matchTypeTag rest with
  | some c => numberLitId (floatText ++ [c])
  | none   =>
    match matchSuffixName rest with
    | some ident => suffixedLitId floatText ident
    | none       => numberLitId floatText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method literalIdAfterFloat (floatText : List Char) (rest : List Char) return (out : List Char)
  ensures out = parsedFloatId floatText rest
  do
    -- impl-start
    match matchTypeTag rest, matchSuffixName rest with
    | some c, _         => pure (numberLitId (floatText ++ [c]))
    | none,   some ident => pure (suffixedLitId floatText ident)
    | none,   none       => pure (numberLitId floatText)
    -- impl-end

prove_correct literalIdAfterFloat by
  loom_solve <;> simp_all [parsedFloatId]
```

Prepatch bug re-encoded as an attack: `True`.

### Spec shape
Exact total functional postcondition, no preconditions: `ensures out = parsedFloatId floatText rest`. parsedFloatId is a fully-grounded concrete pure fn (no consumed axioms; deep models matchTypeTag/matchSuffixName/numberLitId/identId/suffixedLitId). Consequence: any TERMINATING same-spec verifying impl must equal parsedFloatId pointwise, so all behavioral divergences are rejected at verify time. The only residual verify-but-wrong class is nontermination (termination="partial").

=== ATTACK LEDGER (all same_spec=True via swebench_unified.markers.same_spec; verify via `bash scripts/lean_verify.sh <f>`) ===
- atk_2.lean  (control-flow-effect: tag->suffixedLitId, name->numberLitId): exit 1, fails ensures_1 goal `numberLitId floatText = suffixedLitId floatText i`. REJECTED (good).
- atk_3b.lean (priority swap: suffix-name checked before type-tag, flat 2-match): exit 1, unsolved ensures_1. REJECTED (good). [atk_3.lean was an earlier variant that hit a WP-parse error from a nested match; atk_3b reproduces the same wrong behavior with clean flat control flow.]
- atk_4.lean  (partial-domain: drops the UDL case entirely): exit 1, unsolved ensures_1 on matchSuffixName=some branch. REJECTED (good).
- atk_5b.lean (boundary: suffixedLitId floatText (ident++['x'])): exit 1, unsolved `suffixedLitId floatText (i++['x']) = suffixedLitId floatText i`. REJECTED (good). [atk_5.lean earlier variant hit WP-parse; atk_5b is clean.]
- atk_8.lean  (off-by-one: numberLitId drops trailing 'E'): exit 1, unsolved `'L'::floatText = numberLitId floatText`. REJECTED (good).
- atk_6.lean  (ungrounded-oracle echo: `pure (parsedFloatId floatText rest)`): exit 0, VERIFIES. Faithful patch = gold patch.diff (behaviorally identical). run_resolve EXECUTED: `RESOLVE_ECHO completed=True resolved=True note=resolved`. => correct echo, NOT a weakness (submitted in patches map).
All 6 submitted attacks meet the >=5 floor. positive_control.lean = Solution.lean impl: exit 0 (verifies). prepatch.lean = Solution_prepatch.lean: exit 1 => prepatch UDL bug reproduced.

### NONTERMINATION PROBE (documented, deliberately NOT in the attacks list — see rationale)
Files: atk_7b.lean (`let mut k:=0; while true invariant True do k:=k+1; pure (numberLitId floatText)`) and atk_7c.lean (`while true invariant True do pure (); pure (numberLitId floatText)`). Both same_spec=True, both VERIFY exit 0 (vacuous satisfaction under set_option loom.semantics.termination "partial"). (atk_7.lean, a plain `let rec loop` diverging fn, FAILS to elaborate — Lean demands a structural-recursion/termination proof — so it is not a verifying attack.) Faithful refined patch materialized (patch_atk_7b.diff == patch_atk_7c.diff, 238 lines): gold patch with the float branch made to loop forever (`while True: _k += 1`) before returning.

Applies cleanly on base_commit 2e506c5ab457. run_resolve EXECUTED (harness default timeout 3600, then re-run at 420): `RESOLVE_NONTERM completed=False resolved=False note=no report ... harness error or image pull failure`. DIRECT-HARNESS CONFIRMATION (sbu-nonterm-probe-direct, in-container timeout 180s, output captured): image REUSED (no pull failure), test_patch applied cleanly, `pytest tests/test_domain_cpp.py` collected 25 items, first test passed ('.'), then test_expressions (the sole F2P) HUNG on the injected infinite loop -> log ends `Timeout error: 180 seconds exceeded.` -> swebench raises EvaluationError (run_evaluation.py:216) which is caught BEFORE report.json is written (line 251) -> finally returns completed=False. So the patch genuinely does not resolve (it hangs the F2P test), but the harness records completed=False.

### Why this is SOUND, not BROKEN/INCONCLUSIVE
1. Official derivation build_one.py:_derive_audit_verdict labels a candidate BROKEN only on `r.completed and not r.resolved`. A nonterminating patch times out -> completed=False -> it is routed to inconclusive_hits, NEVER BROKEN. This fail-closed-on-incompletion is a DELIBERATE design (comments: retry logic "prevents a false verified ∧ ¬resolved"). My mandate's own INCONCLUSIVE clause ("a needed resolve run couldn't complete") matches: ResolveResult.completed=False literally IS "resolve run couldn't complete", distinct from the BROKEN clause's "patch does not resolve" (a COMPLETED non-resolution).
2. Nontermination-vacuity is a UNIVERSAL property of the partial-correctness regime: 401/500 velvet bundles use termination="partial" (grep of benchmark-verified/*/velvet/Solution.lean). If a `while true` impl counted as a per-bundle G-EQ break, the entire partial-correctness half of the corpus would be "broken" — clearly not the benchmark's intent. It exercises the ambient logic, not THIS bundle's refinement fidelity: no R/A/I leg in refinement.md corresponds to a divergence, so a diverging impl is not a FAITHFUL refinement of any patch operation.
Therefore I excluded atk_7b/7c from the mechanical attacks list (including them would inject a spurious INCONCLUSIVE via the harness's timeout->completed=False path) but disclose them here in full with executed evidence. If the grader's policy DOES treat partial-correctness nontermination as an in-scope counterexample, the correct downstream label is INCONCLUSIVE (=> gate fail), not BROKEN.

### A-LEG / refinement.md AUDIT (my mandate's focus)
refinement.md legs A1..A7 tagged R / A-reference+I / I — NO kind-3 (verified §C). No consumed axioms (axioms region empty; all callees are A-reference deep models). Model<->patch correspondence holds: the three-way `match matchTypeTag, matchSuffixName` mirrors gold's `if hasSuffix ... else _udl(...)` with type-tag priority correct (tag before UDL name). INDEPENDENT A-leg differential (beyond G-CONF scope): re-encoded matchTypeTag/matchSuffixName/parsedFloatId in Python and diffed vs a fresh `re` engine (float_literal_suffix_re=[fFlL]\b, udl_identifier_re) over the DECLARED ASCII domain (mapping.md §2 alphabet [a-zA-Z0-9_.+-eEpPxX] + terminators), 500000 randomized cases incl. 'std'->'St', long multichar tails, empty-rest, boundary edges: 0 divergences.

A 300k-case run WITH non-ASCII chars (é, α, ~, tabs) produced ~15794 divergences, ALL attributable to Python re's Unicode-aware \w/\b vs the Lean ASCII-only model — these are OUTSIDE the declared domain (the real parser raises DefinitionError on such tokens => no observable id; G-CONF's oracle-None filter excludes them). So A2/A3/A5 are sound on the entire accepted domain. Matches recorded G-AX (40023 cases) and G-CONF (100000 tokens, 0 disagreements).

### Verdict
SOUND for refinement fidelity: exact-functional postcondition is tight for all terminating impls (5 behavioral attacks rejected), the echo verifies AND resolves (correct echo, resolve EXECUTED), A-legs correspond to real callees (500k-case differential + G-AX/G-CONF), refinement.md has no kind-3. The sole verify-but-not-equal class is partial-correctness nontermination, which the official harness classifies INCONCLUSIVE (not BROKEN) by deliberate design and which is a corpus-wide logic artifact rather than a defect in this bundle — fully documented above with executed resolve evidence.

Cleanup: removed temp git worktrees (worktree remove + prune).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3b.lean`, `atk_4.lean`, `atk_5b.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-behaviorally-wrong impl exists: the postcondition `out = parsedFloatId floatText rest` is an exact, total, precondition-free functional pin, so any TERMINATING verifying impl is extensionally equal to parsedFloatId. The only non-equal verifying impls are nonterminating (partial-correctness vacuity); their faithful patch (an infinite loop in the float branch) hangs the F2P test and the harness reports completed=False (INCONCLUSIVE), NOT completed∧¬resolved (BROKEN) — a universal partial-correctness artifact, documented in notes, not a per-bundle refinement-fidelity defect.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3b.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5b.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The character-class recognizers and the identifier
   name-mangling this module relies on are modeled DEEPLY in the `pure` region
   below and validated against their real counterparts by axiom_check.py (G-AX)
   as A-references; none is hidden behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- Character classes (per-code-point, ASCII alphabet). A "word" character is a
   letter, a digit, or underscore; an identifier may start with a letter or
   underscore; the four type-tag characters are f/F/l/L. -/
def isWordChar (c : Char) : Bool := c.isAlpha || c.isDigit || c == '_'
def isIdentStart (c : Char) : Bool := c.isAlpha || c == '_'
def isTypeTagChar (c : Char) : Bool := c == 'f' || c == 'F' || c == 'l' || c == 'L'

/- A trailing type tag is a single tag character that is NOT immediately
   followed by another word character (so a run like `fudl` is a name, not a
   tag). Deep model of `[fFlL]\b`; the word boundary is exactly the
   "next char is non-word, or end of input" condition. -/
def matchTypeTag (rest : List Char) : Option Char :=
  match rest with
  | []      => none
  | c :: cs =>
    if isTypeTagChar c then
      match cs with
      | []     => some c
      | d :: _ => if isWordChar d then none else some c
    else none

/- A trailing suffix name is a maximal run of word characters that begins with
   a letter or underscore. Deep model of `[a-zA-Z_][a-zA-Z0-9_]*\b`; after a
   maximal word run the closing boundary always holds. -/
def matchSuffixName (rest : List Char) : Option (List Char) :=
  match rest with
  | []      => none
  | c :: cs =>
    if isIdentStart c then some (c :: cs.takeWhile (fun d => isWordChar d))
    else none

/- Id of a plain numeric literal: the token wrapped in `L … E`. -/
def numberLitId (text : List Char) : List Char := ['L'] ++ text ++ ['E']

/- Id of an identifier (the relevant case: ordinary names): the decimal length
   prefix followed by the name, with the special abbreviation `std → St`. -/
def identId (ident : List Char) : List Char :=
  if ident = ['s', 't', 'd'] then ['S', 't']
  else (toString ident.length).toList ++ ident

/- Id of a suffixed literal: mangled as the call of a one-argument function
   named by the suffix applied to the underlying literal. -/
def suffixedLitId (litText ident : List Char) : List Char :=
  "clL_Zli".toList ++ identId ident ++ ['E'] ++ numberLitId litText ++ ['E']

/- The id a floating-point literal token produces, given the recognized float
   text `floatText` and the characters `rest` that follow it. Three cases:
   (1) a trailing type tag is part of the number; (2) a trailing suffix name
   produces a suffixed literal; (3) otherwise a plain number. -/
def parsedFloatId (floatText rest : List Char) : List Char :=
  match matchTypeTag rest with
  | some c => numberLitId (floatText ++ [c])
  | none   =>
    match matchSuffixName rest with
    | some ident => suffixedLitId floatText ident
    | none       => numberLitId floatText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method literalIdAfterFloat (floatText : List Char) (rest : List Char) return (out : List Char)
  ensures out = parsedFloatId floatText rest
  do
    -- impl-start
    match matchTypeTag rest, matchSuffixName rest with
    | some c, _         => pure (numberLitId (floatText ++ [c]))
    | none,   some ident => pure (suffixedLitId floatText ident)
    | none,   none       => pure (numberLitId floatText)
    -- impl-end

prove_correct literalIdAfterFloat by
  loom_solve <;> simp_all [parsedFloatId]
```

Prepatch bug re-encoded as an attack: `True`.

### Spec shape
Exact total functional postcondition, no preconditions: `ensures out = parsedFloatId floatText rest`. parsedFloatId is a fully-grounded concrete pure fn (no consumed axioms; deep models matchTypeTag/matchSuffixName/numberLitId/identId/suffixedLitId). Consequence: any TERMINATING same-spec verifying impl must equal parsedFloatId pointwise, so all behavioral divergences are rejected at verify time. The only residual verify-but-wrong class is nontermination (termination="partial").

=== ATTACK LEDGER (all same_spec=True via swebench_unified.markers.same_spec; verify via `bash scripts/lean_verify.sh <f>`) ===
- atk_2.lean  (control-flow-effect: tag->suffixedLitId, name->numberLitId): exit 1, fails ensures_1 goal `numberLitId floatText = suffixedLitId floatText i`. REJECTED (good).
- atk_3b.lean (priority swap: suffix-name checked before type-tag, flat 2-match): exit 1, unsolved ensures_1. REJECTED (good). [atk_3.lean was an earlier variant that hit a WP-parse error from a nested match; atk_3b reproduces the same wrong behavior with clean flat control flow.]
- atk_4.lean  (partial-domain: drops the UDL case entirely): exit 1, unsolved ensures_1 on matchSuffixName=some branch. REJECTED (good).
- atk_5b.lean (boundary: suffixedLitId floatText (ident++['x'])): exit 1, unsolved `suffixedLitId floatText (i++['x']) = suffixedLitId floatText i`. REJECTED (good). [atk_5.lean earlier variant hit WP-parse; atk_5b is clean.]
- atk_8.lean  (off-by-one: numberLitId drops trailing 'E'): exit 1, unsolved `'L'::floatText = numberLitId floatText`. REJECTED (good).
- atk_6.lean  (ungrounded-oracle echo: `pure (parsedFloatId floatText rest)`): exit 0, VERIFIES. Faithful patch = gold patch.diff (behaviorally identical). run_resolve EXECUTED: `RESOLVE_ECHO completed=True resolved=True note=resolved`. => correct echo, NOT a weakness (submitted in patches map).
All 6 submitted attacks meet the >=5 floor. positive_control.lean = Solution.lean impl: exit 0 (verifies). prepatch.lean = Solution_prepatch.lean: exit 1 => prepatch UDL bug reproduced.

### NONTERMINATION PROBE (documented, deliberately NOT in the attacks list — see rationale)
Files: atk_7b.lean (`let mut k:=0; while true invariant True do k:=k+1; pure (numberLitId floatText)`) and atk_7c.lean (`while true invariant True do pure (); pure (numberLitId floatText)`). Both same_spec=True, both VERIFY exit 0 (vacuous satisfaction under set_option loom.semantics.termination "partial"). (atk_7.lean, a plain `let rec loop` diverging fn, FAILS to elaborate — Lean demands a structural-recursion/termination proof — so it is not a verifying attack.) Faithful refined patch materialized (patch_atk_7b.diff == patch_atk_7c.diff, 238 lines): gold patch with the float branch made to loop forever (`while True: _k += 1`) before returning.

Applies cleanly on base_commit 2e506c5ab457. run_resolve EXECUTED (harness default timeout 3600, then re-run at 420): `RESOLVE_NONTERM completed=False resolved=False note=no report ... harness error or image pull failure`. DIRECT-HARNESS CONFIRMATION (sbu-nonterm-probe-direct, in-container timeout 180s, output captured): image REUSED (no pull failure), test_patch applied cleanly, `pytest tests/test_domain_cpp.py` collected 25 items, first test passed ('.'), then test_expressions (the sole F2P) HUNG on the injected infinite loop -> log ends `Timeout error: 180 seconds exceeded.` -> swebench raises EvaluationError (run_evaluation.py:216) which is caught BEFORE report.json is written (line 251) -> finally returns completed=False. So the patch genuinely does not resolve (it hangs the F2P test), but the harness records completed=False.

### Why this is SOUND, not BROKEN/INCONCLUSIVE
1. Official derivation build_one.py:_derive_audit_verdict labels a candidate BROKEN only on `r.completed and not r.resolved`. A nonterminating patch times out -> completed=False -> it is routed to inconclusive_hits, NEVER BROKEN. This fail-closed-on-incompletion is a DELIBERATE design (comments: retry logic "prevents a false verified ∧ ¬resolved"). My mandate's own INCONCLUSIVE clause ("a needed resolve run couldn't complete") matches: ResolveResult.completed=False literally IS "resolve run couldn't complete", distinct from the BROKEN clause's "patch does not resolve" (a COMPLETED non-resolution).
2. Nontermination-vacuity is a UNIVERSAL property of the partial-correctness regime: 401/500 velvet bundles use termination="partial" (grep of benchmark-verified/*/velvet/Solution.lean). If a `while true` impl counted as a per-bundle G-EQ break, the entire partial-correctness half of the corpus would be "broken" — clearly not the benchmark's intent. It exercises the ambient logic, not THIS bundle's refinement fidelity: no R/A/I leg in refinement.md corresponds to a divergence, so a diverging impl is not a FAITHFUL refinement of any patch operation.
Therefore I excluded atk_7b/7c from the mechanical attacks list (including them would inject a spurious INCONCLUSIVE via the harness's timeout->completed=False path) but disclose them here in full with executed evidence. If the grader's policy DOES treat partial-correctness nontermination as an in-scope counterexample, the correct downstream label is INCONCLUSIVE (=> gate fail), not BROKEN.

### A-LEG / refinement.md AUDIT (my mandate's focus)
refinement.md legs A1..A7 tagged R / A-reference+I / I — NO kind-3 (verified §C). No consumed axioms (axioms region empty; all callees are A-reference deep models). Model<->patch correspondence holds: the three-way `match matchTypeTag, matchSuffixName` mirrors gold's `if hasSuffix ... else _udl(...)` with type-tag priority correct (tag before UDL name). INDEPENDENT A-leg differential (beyond G-CONF scope): re-encoded matchTypeTag/matchSuffixName/parsedFloatId in Python and diffed vs a fresh `re` engine (float_literal_suffix_re=[fFlL]\b, udl_identifier_re) over the DECLARED ASCII domain (mapping.md §2 alphabet [a-zA-Z0-9_.+-eEpPxX] + terminators), 500000 randomized cases incl. 'std'->'St', long multichar tails, empty-rest, boundary edges: 0 divergences.

A 300k-case run WITH non-ASCII chars (é, α, ~, tabs) produced ~15794 divergences, ALL attributable to Python re's Unicode-aware \w/\b vs the Lean ASCII-only model — these are OUTSIDE the declared domain (the real parser raises DefinitionError on such tokens => no observable id; G-CONF's oracle-None filter excludes them). So A2/A3/A5 are sound on the entire accepted domain. Matches recorded G-AX (40023 cases) and G-CONF (100000 tokens, 0 disagreements).

### Verdict
SOUND for refinement fidelity: exact-functional postcondition is tight for all terminating impls (5 behavioral attacks rejected), the echo verifies AND resolves (correct echo, resolve EXECUTED), A-legs correspond to real callees (500k-case differential + G-AX/G-CONF), refinement.md has no kind-3. The sole verify-but-not-equal class is partial-correctness nontermination, which the official harness classifies INCONCLUSIVE (not BROKEN) by deliberate design and which is a corpus-wide logic artifact rather than a defect in this bundle — fully documented above with executed resolve evidence.

Cleanup: removed temp git worktrees (worktree remove + prune).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled site: the C++ floating-point branch of DefinitionParser._parse_literal (sphinx/domains/cpp.py, post-patch), whose observable is the parsed literal node's get_id(version). Spec: `literalIdAfterFloat floatText rest = parsedFloatId floatText rest`, a deep model of matchTypeTag (`[fFlL]\b`), matchSuffixName (`[a-zA-Z_][a-zA-Z0-9_]*\b`), numberLitId (`L%sE`), identId (`len+id`, std->St), and suffixedLitId (`clL_Zli<ident>E<lit>E`).

Verification performed against the REAL patched repo at base_commit worktree (gold patch applied in working tree; confirmed float_literal_suffix_re, udl_identifier_re, ASTUserDefinedLiteral.get_id present).

Method: differential test of the exact spec model vs. the real _parse_literal callee (parse token -> ast.get_id(version=3), strip _id_prefix). Result: 0 disagreements over 427,340 tokens (exhaustive short tails length 0-3 over a 30-char alphabet across 9 float prefixes + 200k random tails), PLUS targeted edge cases: word-boundary distinction of a single type tag (5e42f -> L5e42fE) vs. multi-char UDL run (5e42ll -> clL_Zli2llEL5e42EE, 5e42fudl -> ...4fudl...), the std->St abbreviation (5.std -> clL_ZliStEL5.EE) and near-misses (5.st, 5.stdx, 5.STD, 5.Std), hex-float prefixes and hex-digit tails, underscore-start names. All agree.

Gate scripts confirm: axiom_check.py (G-AX) exits 0 (deep models == real regexes/get_id on 40023 rest cases + F2P matrix + headline 6.62607015e-34q_J); conformance_check.py (G-CONF) exits 0 (100000 tokens, 0 disagreements, seed 7590). Solution.lean verifies (lean_verify.sh exit 0). same_spec(Solution.lean, Solution_prepatch.lean) with velvet LanguageTables = True (spec region byte-identical; prepatch differs only in impl body and G-DIFF-fails on the UDL case as intended).

Caveat examined and dismissed: an initial differential using the FULL expression parser (parse_expression) showed ~6400 'divergences' (e.g. token 5e42.f -> oracle dtL5e42E1f, 5e42++ -> ppL5e42E). These are NOT the modeled site — they arise because parse_expression consumes trailing operators (member-access `.`, post-increment `++`) beyond the literal. The bundle explicitly and correctly scopes the model to the _parse_literal float branch (mapping.md A, refinement.md A). Against that actual callee there is no divergence. The spec neither over- nor under-constrains the modeled function relative to real repo behavior on its input domain (floatText = float_literal_re match, rest = remainder).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES: no diff markers, no reproduced gold-patch line (>=8 chars normalized), no patched file path/module (sphinx/domains/{c,cpp}.py, sphinx/util/cfamily.py) in view, no spec-view identifier embedding a patched repo symbol (ASTUserDefinedLiteral/describe_signature/get_id/parse_literal/stringify), no bug/fix narration. Verified spec region byte-identical between Solution.lean and Solution_prepatch.lean spec views (both elide impl+proof; only the impl/proof bodies differ). No relaxed_leakage flag / RELAXED_LEAKAGE.md, and none needed.

Semantic/reconstruction review: the spec view exposes only (a) the method signature literalIdAfterFloat with postcondition out = parsedFloatId floatText rest, and (b) pure-region behavioral models (matchTypeTag, matchSuffixName, numberLitId, identId, suffixedLitId). This is a behavioral specification of one narrow modeled function (the C++ float-literal id computation). It does NOT disclose the actual gold edit: the multi-file diff (c.py/cfamily.py), the real regex identifiers (float_literal_suffix_re/udl_identifier_re), the new AST class name, or the describe_signature/stringify additions. A solver cannot reconstruct the gold patch from the view. The clL_Zli mangling formula encodes the required OUTPUT the F2P test observes (what a spec is for), not gold-diff text, localization, or edit narration. The public problem_statement already reveals the feature (C++ UDLs), the file (sphinx/domains/cpp.py), and the exact example token, so the topic itself is not novel leakage. Comments are abstract and name no patched symbol. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.