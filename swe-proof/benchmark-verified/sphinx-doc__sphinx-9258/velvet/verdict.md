# P2 adversarial audit — sphinx-doc__sphinx-9258

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_empty.lean`, `atk_3_classflip.lean`, `atk_4_reverse.lean`, `atk_5_onechar.lean`, `atk_6_offbyone.lean`, `atk_7_dropseps.lean`, `atk_9_contentstep.lean`, `atk_11_asciiws.lean`, `atk_12_lazysep.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo.lean`, `atk_10_reshape.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -173,6 +173,11 @@
   ensures out = splitUnionType target
   do
     -- impl-start
+    -- Pre-image skeleton: the recognized separator set does NOT include the
+    -- vertical-bar form (pipeSep = false), so a `bytes | str`-style field is
+    -- scanned as a single content run instead of three pieces. The frozen spec
+    -- requires the full separator set (pipeSep = true), so prove_correct MUST
+    -- fail on the discriminating step.
     let mut result : List Token := []
     let mut rest := target
     while rest ≠ []
@@ -180,8 +185,8 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      let L := stepLen false rest
+      result := result ++ [⟨rest.take L, delimLen false rest == 0⟩]
       rest := rest.drop L
     return result
     -- impl-end
```

Attack 2 — `atk_2_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -173,16 +173,7 @@
   ensures out = splitUnionType target
   do
     -- impl-start
-    let mut result : List Token := []
-    let mut rest := target
-    while rest ≠ []
-      invariant result ++ splitTokens true rest = splitUnionType target
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
-      rest := rest.drop L
+    let result : List Token := []
     return result
     -- impl-end
 
```

Attack 3 — `atk_3_classflip.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,7 +181,7 @@
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      result := result ++ [⟨rest.take L, delimLen true rest != 0⟩]
       rest := rest.drop L
     return result
     -- impl-end
```

Attack 4 — `atk_4_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,7 +181,7 @@
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      result := [⟨rest.take L, delimLen true rest == 0⟩] ++ result
       rest := rest.drop L
     return result
     -- impl-end
```

Attack 5 — `atk_5_onechar.lean` → rejected (same spec, does not verify — good)

```diff
@@ -180,9 +180,8 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
-      rest := rest.drop L
+      result := result ++ [⟨rest.take 1, delimLen true rest == 0⟩]
+      rest := rest.drop 1
     return result
     -- impl-end
 
```

Attack 6 — `atk_6_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -182,7 +182,7 @@
     do
       let L := stepLen true rest
       result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
-      rest := rest.drop L
+      rest := rest.drop (L + 1)
     return result
     -- impl-end
 
```

Attack 7 — `atk_7_dropseps.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,7 +181,8 @@
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      if delimLen true rest == 0 then
+        result := result ++ [⟨rest.take L, true⟩]
       rest := rest.drop L
     return result
     -- impl-end
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -173,16 +173,7 @@
   ensures out = splitUnionType target
   do
     -- impl-start
-    let mut result : List Token := []
-    let mut rest := target
-    while rest ≠ []
-      invariant result ++ splitTokens true rest = splitUnionType target
-      done_with rest = []
-      decreasing rest.length
-    do
-      let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
-      rest := rest.drop L
+    let result : List Token := splitUnionType target
     return result
     -- impl-end
 
```

Attack 9 — `atk_9_contentstep.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,7 +181,7 @@
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      result := result ++ [⟨rest.take L, contentLen true rest == 0⟩]
       rest := rest.drop L
     return result
     -- impl-end
```

Attack 10 — `atk_10_reshape.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,14 +176,14 @@
     let mut result : List Token := []
     let mut rest := target
     while rest ≠ []
-      invariant result ++ splitTokens true rest = splitUnionType target
+      invariant result.reverse ++ splitTokens true rest = splitUnionType target
       done_with rest = []
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      result := ⟨rest.take L, delimLen true rest == 0⟩ :: result
       rest := rest.drop L
-    return result
+    return result.reverse
     -- impl-end
 
 prove_correct splitUnionTypeField by
```

Attack 11 — `atk_11_asciiws.lean` → rejected (same spec, does not verify — good)

```diff
@@ -181,8 +181,10 @@
       decreasing rest.length
     do
       let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
-      rest := rest.drop L
+      -- treat a leading NON-ASCII space as ordinary content instead of separator
+      let L' := if rest.any (fun c => c.toNat = 0xa0) then 1 else L
+      result := result ++ [⟨rest.take L', delimLen true rest == 0⟩]
+      rest := rest.drop L'
     return result
     -- impl-end
 
```

Attack 12 — `atk_12_lazysep.lean` → rejected (same spec, does not verify — good)

```diff
@@ -180,8 +180,9 @@
       done_with rest = []
       decreasing rest.length
     do
-      let L := stepLen true rest
-      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
+      let d := delimLen true rest
+      let L := if d = 0 then contentLen true rest else max 1 (d - wsLen (rest.drop d))
+      result := result ++ [⟨rest.take L, d == 0⟩]
       rest := rest.drop L
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One element of the split-and-classified type-field stream: the raw text of a
   piece as the splitter produced it, and whether that piece is a member handed
   on as a linked type reference (`linked = true`) or a separator kept as-is
   (`linked = false`). -/
structure Token where
  text : List Char
  linked : Bool
deriving DecidableEq, Inhabited

/- The whitespace class used when scanning a type field: the full Unicode
   whitespace set of the scanner (the 29 code points U+0009–U+000D,
   U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
   U+202F, U+205F, U+3000), so non-ASCII spaces such as the no-break space
   U+00A0 around a bar (e.g. `int<U+00A0>|<U+00A0>str`) are part of the separator. -/
def isWS (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n = 0x85 || n = 0xa0 || n = 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n = 0x2028 || n = 0x2029 ||
  n = 0x202f || n = 0x205f || n = 0x3000

/- The grouping/sequence punctuation recognized as separators: `[ ] ( ) ,`. -/
def isBracket (c : Char) : Bool :=
  c = '[' || c = ']' || c = '(' || c = ')' || c = ','

/- Length of the leading run of whitespace. -/
def wsLen : List Char → Nat
  | [] => 0
  | c :: cs => if isWS c then 1 + wsLen cs else 0

/- A literal ellipsis `...` separator. -/
def delimEllipsis (s : List Char) : Nat :=
  match s with
  | '.' :: '.' :: '.' :: _ => 3
  | _ => 0

/- The vertical-bar separator `<ws> | <ws>`, recognized at the front only when
   the bar is enabled as a separator (`pipeSep = true`). When disabled, fall
   through to the ellipsis separator. The bar is the union-type separator from
   the problem statement (e.g. `bytes | str`). -/
def delimPipe (pipeSep : Bool) (s : List Char) : Nat :=
  if pipeSep then
    let w1 := wsLen s
    match s.drop w1 with
    | '|' :: rest => w1 + 1 + wsLen rest
    | _ => delimEllipsis s
  else delimEllipsis s

/- The word separator `<ws+> or <ws+>` (the "or" join), tried after the bracket
   form; on no match, defer to the bar / ellipsis separators. -/
def delimOr (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  if w1 ≥ 1 then
    match s.drop w1 with
    | 'o' :: 'r' :: rest =>
      let w2 := wsLen rest
      if w2 ≥ 1 then w1 + 2 + w2 else delimPipe pipeSep s
    | _ => delimPipe pipeSep s
  else delimPipe pipeSep s

/- Length of the separator matched at the front of `s` under the configured
   separator set, by greedy maximal munch in priority order — bracket/comma form
   (with optional surrounding whitespace and an optional ` or ` infix), then the
   ` or ` word form, then the bar form (if enabled), then the ellipsis. Returns
   0 when the front of `s` is ordinary content (the start of a type reference). -/
def delimLen (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  match s.drop w1 with
  | b :: rest =>
    if isBracket b then
      let w2 := wsLen rest
      let afterW2 := rest.drop w2
      let optLen :=
        match afterW2 with
        | 'o' :: 'r' :: c3 :: _ => if isWS c3 then w2 + 2 + 1 else 0
        | _ => 0
      let afterOpt := rest.drop optLen
      let w3 := wsLen afterOpt
      w1 + 1 + optLen + w3
    else delimOr pipeSep s
  | [] => delimOr pipeSep s

/- Length of the leading content run: characters up to (but not including) the
   next separator. Zero iff a separator starts at the front. -/
def contentLen (pipeSep : Bool) : List Char → Nat
  | [] => 0
  | c :: cs => if delimLen pipeSep (c :: cs) = 0 then 1 + contentLen pipeSep cs else 0

/- One forward step: consume a separator run if one matches at the front,
   otherwise consume the maximal content run. Strictly positive on nonempty
   input (`stepLen_pos`), which drives both termination and the loop's progress. -/
def stepLen (pipeSep : Bool) (s : List Char) : Nat :=
  if delimLen pipeSep s = 0 then contentLen pipeSep s else delimLen pipeSep s

/- A nonempty type field always advances by at least one character: either a
   separator (delimLen ≥ 1) or one content char (contentLen ≥ 1). -/
theorem stepLen_pos {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    1 ≤ stepLen pipeSep s := by
  cases s with
  | nil => exact absurd rfl h
  | cons c cs =>
    unfold stepLen
    split
    · rename_i hd; simp only [contentLen, hd, if_true]; omega
    · rename_i hd; omega

/- One step off a nonempty type field STRICTLY shortens the remaining input: the
   step consumes at least one character (`stepLen_pos`), so dropping it lowers
   the length. This is the loop's actual progress, and it is what discharges the
   `decreasing rest.length` obligation that TOTAL-correctness semantics emits for
   the `while` below (under `open TotalCorrectness` the measure is a real proof
   obligation, not an annotation). -/
theorem stepLen_drop_length_lt {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    (s.drop (stepLen pipeSep s)).length < s.length := by
  have h1 := stepLen_pos (pipeSep := pipeSep) h
  have hlen : 0 < s.length := by
    cases s with | nil => exact absurd rfl h | cons _ _ => simp
  simp only [List.length_drop]; omega

/- The full split-and-classify of a type field, front-recursively: peel one
   step off the front, emit a token for that piece (linked iff it is content,
   i.e. `delimLen = 0`), and recurse on the remainder. This is the per-element
   expansion of the input the result is the concatenation of (the fold pattern,
   plan §5.4). Deep model of the `re` split pipeline; G-AX validates
   `splitTokens true` against the real engine (mapping.md §3.1). -/
def splitTokens (pipeSep : Bool) (s : List Char) : List Token :=
  if h : s = [] then []
  else
    ⟨s.take (stepLen pipeSep s), delimLen pipeSep s == 0⟩
      :: splitTokens pipeSep (s.drop (stepLen pipeSep s))
termination_by s.length
decreasing_by
  exact stepLen_drop_length_lt (pipeSep := pipeSep) h

@[grind] theorem splitTokens_nil (p : Bool) : splitTokens p [] = [] := by
  unfold splitTokens; simp

/- The single front-unfold the loop body needs: one step off a nonempty field
   exposes the head token and the split of the remainder. -/
@[grind] theorem splitTokens_cons {p : Bool} {s : List Char} (h : s ≠ []) :
    splitTokens p s
      = ⟨s.take (stepLen p s), delimLen p s == 0⟩ :: splitTokens p (s.drop (stepLen p s)) := by
  conv_lhs => unfold splitTokens
  simp [h]

/- The type field split-and-classified into its piece stream: separated members
   are the pieces handed on as linked type references; the separators between
   them (commas, brackets, the word join, the vertical bar of `a | b`, ellipses)
   are kept as verbatim separator pieces. The bar separator is the union-type
   syntax of the problem statement. -/
def splitUnionType (target : List Char) : List Token := splitTokens true target
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method splitUnionTypeField (target : List Char) return (out : List Token)
  ensures out = splitUnionType target
  do
    -- impl-start
    let mut result : List Token := []
    let mut rest := target
    while rest ≠ []
      invariant result ++ splitTokens true rest = splitUnionType target
      done_with rest = []
      decreasing rest.length
    do
      let L := stepLen true rest
      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
      rest := rest.drop L
    return result
    -- impl-end

prove_correct splitUnionTypeField by
  unfold splitUnionType
  loom_solve
  all_goals try exact stepLen_drop_length_lt (by assumption)
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit of velvet bundle sphinx-doc__sphinx-9258. Spec shape: `method splitUnionTypeField (target: List Char) return (out: List Token) ensures out = splitUnionType target` where splitUnionType target = splitTokens true target — a TOTAL functional-equality postcondition with NO precondition, i.e. the tightest possible shape: any verifying impl must reproduce the full maximal-munch split+classify exactly, on every input.

**ADMISSIBILITY:** all 12 attacks + the positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet tables) AND unsound_evasions=[] (no dropped obligation, no new axiom, no sorry/admit). Attacks were built by copying Solution.lean and editing ONLY the impl region.

**COMMANDS:** verification — `bash scripts/lean_verify.sh <SCRATCH>/<file>.lean` (exit 0=verifies, 1=error). Run concurrently as detached background jobs in batches of <=4 per the parallelism protocol (batch1: atk_2,3,4,5; batch2: atk_6,7,8,9; then atk_10; then atk_11,12; pos_control+atk_1 first). Resolve — `python <SCRATCH>/resolve_one.py <name> <patch.diff>` calling harness.run_resolve('sphinx-doc__sphinx-9258', patch, run_id='sbu-geq-q6kd-<name>', timeout=1800); the two resolve runs were launched concurrently.

### ATTACK RESULTS (12 attacks, 5 distinct wrong-impl classes + 2 behaviour-preserving reshapes):
- atk_1_prepatch.lean (PREPATCH BUG re-encoded: stepLen/delimLen `false`, bar NOT a separator): rc=1 REJECTED. Unsolved goal at the discriminating step: `result ++ [{text:= take (stepLen false rest) rest, linked:= delimLen false rest == 0}] ++ splitTokens true (drop (stepLen false rest) rest) = splitTokens true target`. Matches G-DIFF's recorded prepatch failure. prepatch_reproduced=True.
- atk_2_empty.lean (PARTIAL-DOMAIN: `return []`, correct only for the empty field): rc=1 REJECTED. Goal `[] = splitTokens true target`.
- atk_3_classflip.lean (UNGROUNDED-ORACLE / classification inverted: linked:= delimLen != 0): rc=1 REJECTED.
- atk_4_reverse.lean (CONTROL-FLOW-EFFECT: prepend instead of append -> reversed token order): rc=1 REJECTED.
- atk_5_onechar.lean (BOUNDARY: consume exactly 1 char per step, destroying maximal munch so every content run becomes single-char tokens): rc=1 REJECTED.
- atk_6_offbyone.lean (BOUNDARY off-by-one: rest:= rest.drop (L+1), skips a char per step): rc=1 REJECTED.
- atk_7_dropseps.lean (CONTROL-FLOW-EFFECT / partial: emit only the linked members, drop separator tokens — the plausible alternative reading of the fix): rc=1 REJECTED.
- atk_8_echo.lean (UNGROUNDED-ORACLE ECHO: `return splitUnionType target`): rc=0 VERIFIES -> candidate, resolve-checked below.
- atk_9_contentstep.lean (classification via contentLen==0 instead of delimLen==0): rc=1 REJECTED.
- atk_10_reshape.lean (behaviour-PRESERVING reshape: cons-accumulate with invariant on result.reverse, then return result.reverse): rc=0 VERIFIES -> candidate, resolve-checked below.
- atk_11_asciiws.lean (A-LEG TARGETED, partial-domain on the whitespace class: mis-step when a non-ASCII space U+00A0 is present, i.e. the classic under-modeling of regex `\s` as ASCII-only): rc=1 REJECTED.
- atk_12_lazysep.lean (A-LEG TARGETED, greedy-vs-lazy boundary: emit the separator WITHOUT its trailing whitespace run, i.e. `\s*\|\s*` mis-modeled as `\s*\|`): rc=1 REJECTED.

positive_control (pos_control.lean, byte-identical copy of the shipped Solution.lean): rc=0 VERIFIES (only an unused-variable linter warning; no sorry/error).

MANDATORY RESOLVE RUNS — both verifying attacks had their faithful refined patch MATERIALIZED and EXECUTED through the official harness:

(1) atk_8_echo -> patch_atk8_deepmodel.diff. Deliberately the MOST ADVERSARIAL faithful refinement available: instead of the gold one-line regex edit, it refines the echo's `splitUnionType` = `splitTokens true` LITERALLY into Python, replacing re.split/delims_re.match entirely with the transliterated deep model (`_is_ws`/`_ws_len`/`_delim_ellipsis`/`_delim_pipe`/`_delim_or`/`_delim_len`/`_content_len`/`_split_tokens`) and classifying by the model's own `linked` flag. This puts the A-reference leg (refinement.md row A2) directly on trial in the real test suite. OBSERVED: resolved=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS test_info_field_list_piped_type 1/1 SUCCESS; PASS_TO_PASS 45/45 SUCCESS; 0 failures, 0 PASS_TO_FAIL.

(2) atk_10_reshape -> patch_atk10_reshape.diff (gold delims edit + reverse-accumulate/flip node assembly, mirroring the Lean reshape). OBSERVED: resolved=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS 1/1 SUCCESS; PASS_TO_PASS 45/45 SUCCESS; 0 failures.
Both candidates are therefore CORRECT ECHOES, not spec weaknesses. No verifying impl's faithful patch fails to resolve.

A-LEG (axioms / deep-model references) AUDIT — the focus of this role, since R/I is G-CONF's job. The axioms region is EMPTY (meta.json axioms: []), so there is no consumed axiom; the single deep_model_reference is `splitTokens` (kind A-reference). Independent falsification attempts on it, all in scratch:
- Wrote deepmodel.py, a line-by-line transliteration of Solution.lean's pure region, and diffed it against the REAL unchanged CPython re engine under the post-patch delims r'(\s*[\[\]\(\),](?:\`s*or`\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)' with the same filter(None,...) + delims_re.match parity classification: exhaustive all strings of length<6 over a 14-char alphabet {space,|,o,r,.,[,],(,),comma,tab,a,NBSP,newline} = 579,195 inputs -> 0 divergences; seeded fuzz 400,000 inputs len<=25 over a 19-char alphabet incl. U+00A0/U+0085/U+001C/U+3000 -> 0 divergences.
- Whitespace class: compared isWS against Python re `\s` over ALL 0x110000 codepoints -> 0 divergences; the modeled set is exactly 29 code points, matching the docstring's claim verbatim.
- Deep model vs GOLD post-patch token stream on the F2P-relevant fields ('int | str', 'bytes | str', 'int|str', 'int  |  str', 'List[int, str]', 'Tuple[int,...]', 'int or str', 'dict(str, int)') -> all identical; plus 300,000-input fuzz -> 0 divergences.
- Ran the bundle's own G-AX checker: `python3 axiom_check.py` -> rc=0, 'G-AX OK: splitTokens deep model (== real re.split+classify under the post-patch delimiter set) sound on 31 boundary + 50000 fuzz inputs; make_xref text-preservation R-claim holds.'
- The strongest evidence for the A-reference is (1) above: the deep model SUBSTITUTED for the real re engine in the repo passes the entire graded suite (46/46). The A-reference correspondence to the real callee holds.

MODEL<->PATCH CORRESPONDENCE / refinement.md leg audit: every leg is R, A-consumed, A-reference, or I — NO kind-3 (inexpressible-changed-op) step. A1 = R (str <-> List Char, mapping.md §2). A2 = A-reference + I: the one operation that genuinely CHANGED (the delimiter-set split+classify) is modeled DEEPLY by splitTokens/stepLen/delimLen/contentLen in the pure region rather than hidden behind an axiom about the function under change; the model's four alternatives map 1:1 onto the four regex alternatives, with the new bar alternative living in delimPipe's `pipeSep=true` branch; the fold ops (take/drop/++/==/while) are concrete I. A3 = R + I: linked=(delimLen==0) is exactly the capturing-group re.split parity, and the boundary R-claim was CHECKED against the real source — in sphinx/domains/python.py the loop is `for sub_target in filter(None, sub_targets)` and the call is `self.make_xref(rolename, domain, sub_target,...)`, so the piece flows into make_xref verbatim with no rewriting between split and call, as §3.2 asserts.

A4 = R (order-preserving node<->Token bijection). Section B's claim that make_xref is an R-refinement at the call boundary rather than a consumed axiom is correct and is the honest tagging: make_xref is unchanged by the patch and its downstream '.'/'~' short-name rewriting is byte-identical pre/post, carrying no discriminating content; on the F2P fields ('int', 'str') no such prefix occurs so rendered text == boundary string. Section C's no-kind-3 claim holds. Verified mapping.md's line bindings at base_commit 06107f838: make_xref at:285, make_xrefs at:304, delims at:307 — all correct.

**VERDICT:** SOUND. 12 admissible attacks run (>=5 required) spanning partial-domain (atk_2, atk_7, atk_11), boundary (atk_5, atk_6, atk_12), control-flow-effect (atk_4, atk_7), ungrounded-oracle (atk_3, atk_8, atk_9) and the prepatch bug (atk_1); positive control verifies; prepatch reproduced. The two verifying impls are both behaviourally CORRECT (an oracle echo and a semantics-preserving reshape) and BOTH had their faithful refined patches executed through the official harness with resolved=True (46/46 tests). No verifying wrong impl exists whose faithful patch fails to resolve, so verify=>correct is upheld and the spec is NOT broken. The total functional-equality postcondition leaves zero behavioral slack, and the one A-reference leg is independently corroborated by ~1.28M differential inputs, an exhaustive Unicode whitespace comparison, the bundle's G-AX check, and — decisively — a resolve of the deep model substituted for the real re engine.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.lean`, `atk_2_empty.lean`, `atk_3_classflip.lean`, `atk_4_reverse.lean`, `atk_5_onechar.lean`, `atk_6_offbyone.lean`, `atk_7_dropseps.lean`, `atk_9_contentstep.lean`, `atk_11_asciiws.lean`, `atk_12_lazysep.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo.lean`, `atk_10_reshape.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_empty.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_classflip.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_reverse.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_onechar.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_dropseps.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_contentstep.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_reshape.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_asciiws.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_lazysep.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One element of the split-and-classified type-field stream: the raw text of a
   piece as the splitter produced it, and whether that piece is a member handed
   on as a linked type reference (`linked = true`) or a separator kept as-is
   (`linked = false`). -/
structure Token where
  text : List Char
  linked : Bool
deriving DecidableEq, Inhabited

/- The whitespace class used when scanning a type field: the full Unicode
   whitespace set of the scanner (the 29 code points U+0009–U+000D,
   U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
   U+202F, U+205F, U+3000), so non-ASCII spaces such as the no-break space
   U+00A0 around a bar (e.g. `int<U+00A0>|<U+00A0>str`) are part of the separator. -/
def isWS (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n = 0x85 || n = 0xa0 || n = 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n = 0x2028 || n = 0x2029 ||
  n = 0x202f || n = 0x205f || n = 0x3000

/- The grouping/sequence punctuation recognized as separators: `[ ] ( ) ,`. -/
def isBracket (c : Char) : Bool :=
  c = '[' || c = ']' || c = '(' || c = ')' || c = ','

/- Length of the leading run of whitespace. -/
def wsLen : List Char → Nat
  | [] => 0
  | c :: cs => if isWS c then 1 + wsLen cs else 0

/- A literal ellipsis `...` separator. -/
def delimEllipsis (s : List Char) : Nat :=
  match s with
  | '.' :: '.' :: '.' :: _ => 3
  | _ => 0

/- The vertical-bar separator `<ws> | <ws>`, recognized at the front only when
   the bar is enabled as a separator (`pipeSep = true`). When disabled, fall
   through to the ellipsis separator. The bar is the union-type separator from
   the problem statement (e.g. `bytes | str`). -/
def delimPipe (pipeSep : Bool) (s : List Char) : Nat :=
  if pipeSep then
    let w1 := wsLen s
    match s.drop w1 with
    | '|' :: rest => w1 + 1 + wsLen rest
    | _ => delimEllipsis s
  else delimEllipsis s

/- The word separator `<ws+> or <ws+>` (the "or" join), tried after the bracket
   form; on no match, defer to the bar / ellipsis separators. -/
def delimOr (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  if w1 ≥ 1 then
    match s.drop w1 with
    | 'o' :: 'r' :: rest =>
      let w2 := wsLen rest
      if w2 ≥ 1 then w1 + 2 + w2 else delimPipe pipeSep s
    | _ => delimPipe pipeSep s
  else delimPipe pipeSep s

/- Length of the separator matched at the front of `s` under the configured
   separator set, by greedy maximal munch in priority order — bracket/comma form
   (with optional surrounding whitespace and an optional ` or ` infix), then the
   ` or ` word form, then the bar form (if enabled), then the ellipsis. Returns
   0 when the front of `s` is ordinary content (the start of a type reference). -/
def delimLen (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  match s.drop w1 with
  | b :: rest =>
    if isBracket b then
      let w2 := wsLen rest
      let afterW2 := rest.drop w2
      let optLen :=
        match afterW2 with
        | 'o' :: 'r' :: c3 :: _ => if isWS c3 then w2 + 2 + 1 else 0
        | _ => 0
      let afterOpt := rest.drop optLen
      let w3 := wsLen afterOpt
      w1 + 1 + optLen + w3
    else delimOr pipeSep s
  | [] => delimOr pipeSep s

/- Length of the leading content run: characters up to (but not including) the
   next separator. Zero iff a separator starts at the front. -/
def contentLen (pipeSep : Bool) : List Char → Nat
  | [] => 0
  | c :: cs => if delimLen pipeSep (c :: cs) = 0 then 1 + contentLen pipeSep cs else 0

/- One forward step: consume a separator run if one matches at the front,
   otherwise consume the maximal content run. Strictly positive on nonempty
   input (`stepLen_pos`), which drives both termination and the loop's progress. -/
def stepLen (pipeSep : Bool) (s : List Char) : Nat :=
  if delimLen pipeSep s = 0 then contentLen pipeSep s else delimLen pipeSep s

/- A nonempty type field always advances by at least one character: either a
   separator (delimLen ≥ 1) or one content char (contentLen ≥ 1). -/
theorem stepLen_pos {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    1 ≤ stepLen pipeSep s := by
  cases s with
  | nil => exact absurd rfl h
  | cons c cs =>
    unfold stepLen
    split
    · rename_i hd; simp only [contentLen, hd, if_true]; omega
    · rename_i hd; omega

/- One step off a nonempty type field STRICTLY shortens the remaining input: the
   step consumes at least one character (`stepLen_pos`), so dropping it lowers
   the length. This is the loop's actual progress, and it is what discharges the
   `decreasing rest.length` obligation that TOTAL-correctness semantics emits for
   the `while` below (under `open TotalCorrectness` the measure is a real proof
   obligation, not an annotation). -/
theorem stepLen_drop_length_lt {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    (s.drop (stepLen pipeSep s)).length < s.length := by
  have h1 := stepLen_pos (pipeSep := pipeSep) h
  have hlen : 0 < s.length := by
    cases s with | nil => exact absurd rfl h | cons _ _ => simp
  simp only [List.length_drop]; omega

/- The full split-and-classify of a type field, front-recursively: peel one
   step off the front, emit a token for that piece (linked iff it is content,
   i.e. `delimLen = 0`), and recurse on the remainder. This is the per-element
   expansion of the input the result is the concatenation of (the fold pattern,
   plan §5.4). Deep model of the `re` split pipeline; G-AX validates
   `splitTokens true` against the real engine (mapping.md §3.1). -/
def splitTokens (pipeSep : Bool) (s : List Char) : List Token :=
  if h : s = [] then []
  else
    ⟨s.take (stepLen pipeSep s), delimLen pipeSep s == 0⟩
      :: splitTokens pipeSep (s.drop (stepLen pipeSep s))
termination_by s.length
decreasing_by
  exact stepLen_drop_length_lt (pipeSep := pipeSep) h

@[grind] theorem splitTokens_nil (p : Bool) : splitTokens p [] = [] := by
  unfold splitTokens; simp

/- The single front-unfold the loop body needs: one step off a nonempty field
   exposes the head token and the split of the remainder. -/
@[grind] theorem splitTokens_cons {p : Bool} {s : List Char} (h : s ≠ []) :
    splitTokens p s
      = ⟨s.take (stepLen p s), delimLen p s == 0⟩ :: splitTokens p (s.drop (stepLen p s)) := by
  conv_lhs => unfold splitTokens
  simp [h]

/- The type field split-and-classified into its piece stream: separated members
   are the pieces handed on as linked type references; the separators between
   them (commas, brackets, the word join, the vertical bar of `a | b`, ellipses)
   are kept as verbatim separator pieces. The bar separator is the union-type
   syntax of the problem statement. -/
def splitUnionType (target : List Char) : List Token := splitTokens true target
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method splitUnionTypeField (target : List Char) return (out : List Token)
  ensures out = splitUnionType target
  do
    -- impl-start
    let mut result : List Token := []
    let mut rest := target
    while rest ≠ []
      invariant result ++ splitTokens true rest = splitUnionType target
      done_with rest = []
      decreasing rest.length
    do
      let L := stepLen true rest
      result := result ++ [⟨rest.take L, delimLen true rest == 0⟩]
      rest := rest.drop L
    return result
    -- impl-end

prove_correct splitUnionTypeField by
  unfold splitUnionType
  loom_solve
  all_goals try exact stepLen_drop_length_lt (by assumption)
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit of velvet bundle sphinx-doc__sphinx-9258. Spec shape: `method splitUnionTypeField (target: List Char) return (out: List Token) ensures out = splitUnionType target` where splitUnionType target = splitTokens true target — a TOTAL functional-equality postcondition with NO precondition, i.e. the tightest possible shape: any verifying impl must reproduce the full maximal-munch split+classify exactly, on every input.

**ADMISSIBILITY:** all 12 attacks + the positive control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet tables) AND unsound_evasions=[] (no dropped obligation, no new axiom, no sorry/admit). Attacks were built by copying Solution.lean and editing ONLY the impl region.

**COMMANDS:** verification — `bash scripts/lean_verify.sh <SCRATCH>/<file>.lean` (exit 0=verifies, 1=error). Run concurrently as detached background jobs in batches of <=4 per the parallelism protocol (batch1: atk_2,3,4,5; batch2: atk_6,7,8,9; then atk_10; then atk_11,12; pos_control+atk_1 first). Resolve — `python <SCRATCH>/resolve_one.py <name> <patch.diff>` calling harness.run_resolve('sphinx-doc__sphinx-9258', patch, run_id='sbu-geq-q6kd-<name>', timeout=1800); the two resolve runs were launched concurrently.

### ATTACK RESULTS (12 attacks, 5 distinct wrong-impl classes + 2 behaviour-preserving reshapes):
- atk_1_prepatch.lean (PREPATCH BUG re-encoded: stepLen/delimLen `false`, bar NOT a separator): rc=1 REJECTED. Unsolved goal at the discriminating step: `result ++ [{text:= take (stepLen false rest) rest, linked:= delimLen false rest == 0}] ++ splitTokens true (drop (stepLen false rest) rest) = splitTokens true target`. Matches G-DIFF's recorded prepatch failure. prepatch_reproduced=True.
- atk_2_empty.lean (PARTIAL-DOMAIN: `return []`, correct only for the empty field): rc=1 REJECTED. Goal `[] = splitTokens true target`.
- atk_3_classflip.lean (UNGROUNDED-ORACLE / classification inverted: linked:= delimLen != 0): rc=1 REJECTED.
- atk_4_reverse.lean (CONTROL-FLOW-EFFECT: prepend instead of append -> reversed token order): rc=1 REJECTED.
- atk_5_onechar.lean (BOUNDARY: consume exactly 1 char per step, destroying maximal munch so every content run becomes single-char tokens): rc=1 REJECTED.
- atk_6_offbyone.lean (BOUNDARY off-by-one: rest:= rest.drop (L+1), skips a char per step): rc=1 REJECTED.
- atk_7_dropseps.lean (CONTROL-FLOW-EFFECT / partial: emit only the linked members, drop separator tokens — the plausible alternative reading of the fix): rc=1 REJECTED.
- atk_8_echo.lean (UNGROUNDED-ORACLE ECHO: `return splitUnionType target`): rc=0 VERIFIES -> candidate, resolve-checked below.
- atk_9_contentstep.lean (classification via contentLen==0 instead of delimLen==0): rc=1 REJECTED.
- atk_10_reshape.lean (behaviour-PRESERVING reshape: cons-accumulate with invariant on result.reverse, then return result.reverse): rc=0 VERIFIES -> candidate, resolve-checked below.
- atk_11_asciiws.lean (A-LEG TARGETED, partial-domain on the whitespace class: mis-step when a non-ASCII space U+00A0 is present, i.e. the classic under-modeling of regex `\s` as ASCII-only): rc=1 REJECTED.
- atk_12_lazysep.lean (A-LEG TARGETED, greedy-vs-lazy boundary: emit the separator WITHOUT its trailing whitespace run, i.e. `\s*\|\s*` mis-modeled as `\s*\|`): rc=1 REJECTED.

positive_control (pos_control.lean, byte-identical copy of the shipped Solution.lean): rc=0 VERIFIES (only an unused-variable linter warning; no sorry/error).

MANDATORY RESOLVE RUNS — both verifying attacks had their faithful refined patch MATERIALIZED and EXECUTED through the official harness:

(1) atk_8_echo -> patch_atk8_deepmodel.diff. Deliberately the MOST ADVERSARIAL faithful refinement available: instead of the gold one-line regex edit, it refines the echo's `splitUnionType` = `splitTokens true` LITERALLY into Python, replacing re.split/delims_re.match entirely with the transliterated deep model (`_is_ws`/`_ws_len`/`_delim_ellipsis`/`_delim_pipe`/`_delim_or`/`_delim_len`/`_content_len`/`_split_tokens`) and classifying by the model's own `linked` flag. This puts the A-reference leg (refinement.md row A2) directly on trial in the real test suite. OBSERVED: resolved=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS test_info_field_list_piped_type 1/1 SUCCESS; PASS_TO_PASS 45/45 SUCCESS; 0 failures, 0 PASS_TO_FAIL.

(2) atk_10_reshape -> patch_atk10_reshape.diff (gold delims edit + reverse-accumulate/flip node assembly, mirroring the Lean reshape). OBSERVED: resolved=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS 1/1 SUCCESS; PASS_TO_PASS 45/45 SUCCESS; 0 failures.
Both candidates are therefore CORRECT ECHOES, not spec weaknesses. No verifying impl's faithful patch fails to resolve.

A-LEG (axioms / deep-model references) AUDIT — the focus of this role, since R/I is G-CONF's job. The axioms region is EMPTY (meta.json axioms: []), so there is no consumed axiom; the single deep_model_reference is `splitTokens` (kind A-reference). Independent falsification attempts on it, all in scratch:
- Wrote deepmodel.py, a line-by-line transliteration of Solution.lean's pure region, and diffed it against the REAL unchanged CPython re engine under the post-patch delims r'(\s*[\[\]\(\),](?:\`s*or`\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)' with the same filter(None,...) + delims_re.match parity classification: exhaustive all strings of length<6 over a 14-char alphabet {space,|,o,r,.,[,],(,),comma,tab,a,NBSP,newline} = 579,195 inputs -> 0 divergences; seeded fuzz 400,000 inputs len<=25 over a 19-char alphabet incl. U+00A0/U+0085/U+001C/U+3000 -> 0 divergences.
- Whitespace class: compared isWS against Python re `\s` over ALL 0x110000 codepoints -> 0 divergences; the modeled set is exactly 29 code points, matching the docstring's claim verbatim.
- Deep model vs GOLD post-patch token stream on the F2P-relevant fields ('int | str', 'bytes | str', 'int|str', 'int  |  str', 'List[int, str]', 'Tuple[int,...]', 'int or str', 'dict(str, int)') -> all identical; plus 300,000-input fuzz -> 0 divergences.
- Ran the bundle's own G-AX checker: `python3 axiom_check.py` -> rc=0, 'G-AX OK: splitTokens deep model (== real re.split+classify under the post-patch delimiter set) sound on 31 boundary + 50000 fuzz inputs; make_xref text-preservation R-claim holds.'
- The strongest evidence for the A-reference is (1) above: the deep model SUBSTITUTED for the real re engine in the repo passes the entire graded suite (46/46). The A-reference correspondence to the real callee holds.

MODEL<->PATCH CORRESPONDENCE / refinement.md leg audit: every leg is R, A-consumed, A-reference, or I — NO kind-3 (inexpressible-changed-op) step. A1 = R (str <-> List Char, mapping.md §2). A2 = A-reference + I: the one operation that genuinely CHANGED (the delimiter-set split+classify) is modeled DEEPLY by splitTokens/stepLen/delimLen/contentLen in the pure region rather than hidden behind an axiom about the function under change; the model's four alternatives map 1:1 onto the four regex alternatives, with the new bar alternative living in delimPipe's `pipeSep=true` branch; the fold ops (take/drop/++/==/while) are concrete I. A3 = R + I: linked=(delimLen==0) is exactly the capturing-group re.split parity, and the boundary R-claim was CHECKED against the real source — in sphinx/domains/python.py the loop is `for sub_target in filter(None, sub_targets)` and the call is `self.make_xref(rolename, domain, sub_target,...)`, so the piece flows into make_xref verbatim with no rewriting between split and call, as §3.2 asserts.

A4 = R (order-preserving node<->Token bijection). Section B's claim that make_xref is an R-refinement at the call boundary rather than a consumed axiom is correct and is the honest tagging: make_xref is unchanged by the patch and its downstream '.'/'~' short-name rewriting is byte-identical pre/post, carrying no discriminating content; on the F2P fields ('int', 'str') no such prefix occurs so rendered text == boundary string. Section C's no-kind-3 claim holds. Verified mapping.md's line bindings at base_commit 06107f838: make_xref at:285, make_xrefs at:304, delims at:307 — all correct.

**VERDICT:** SOUND. 12 admissible attacks run (>=5 required) spanning partial-domain (atk_2, atk_7, atk_11), boundary (atk_5, atk_6, atk_12), control-flow-effect (atk_4, atk_7), ungrounded-oracle (atk_3, atk_8, atk_9) and the prepatch bug (atk_1); positive control verifies; prepatch reproduced. The two verifying impls are both behaviourally CORRECT (an oracle echo and a semantics-preserving reshape) and BOTH had their faithful refined patches executed through the official harness with resolved=True (46/46 tests). No verifying wrong impl exists whose faithful patch fails to resolve, so verify=>correct is upheld and the spec is NOT broken. The total functional-equality postcondition leaves zero behavioral slack, and the one A-reference leg is independently corroborated by ~1.28M differential inputs, an exhaustive Unicode whitespace comparison, the bundle's G-AX check, and — decisively — a resolve of the deep model substituted for the real re engine.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker (2) faithfulness-break on sphinx-doc__sphinx-9258 / velvet. No divergence found between the modeled function and the real (post-patch) repo callee; verdict FAITHFUL.

**REFERENCE SET UP CORRECTLY.** Worktree of sphinx-doc_sphinx.git at base_commit 06107f838c28ab6ca6bfc2cc208e15997fcb2146 with velvet/../patch.diff APPLIED (confirmed sphinx/domains/python.py:307 now reads delims = r'(\s*[\[\]\(\),](?:\`s*or`\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'). The post-patch tree is the reference for splitUnionType / splitTokens true, per the gate rule; base is reference only for untouched callees. I did NOT compare against base (that would manufacture a divergence on exactly the patch delta).

**WHAT IS MODELED.** splitUnionType target = splitTokens true target: a maximal-munch left-to-right scan emitting Token (text, linked), where linked = (delimLen true = 0). mapping.md binds this to make_xrefs' re.split(delims, target) -> filter(None,...) -> per-piece delims_re.match classification (python.py:307-326). No consumed axiom (axioms region is empty); the split is a DEEP model, so faithfulness is fully mechanically testable rather than resting on an axiom's ensures.

DIFFERENTIAL TESTING (model transliterated op-for-op from the Lean pure region: isWS, isBracket, wsLen, delimEllipsis, delimPipe, delimOr, delimLen, contentLen, stepLen, splitTokens; oracle = verbatim re-implementation of the repo's post-patch lines, re.split(DELIMS,target) + filter(None,..) + not bool(DELIMS_RE.match(piece)), checked line-for-line against python.py:307-326). Total ~1.02M inputs, ZERO mismatches:
  - Exhaustive over all 1,114,112 Unicode codepoints: isWS c == bool(re.match(r'\s', chr(c))) -> 0 mismatches (confirms the 29-codepoint whitespace claim in mapping.md 2 is EXACT for a str-mode pattern, incl. U+0085, U+00A0, U+001C-001F, U+1680, U+2000-200A, U+2028/9, U+202F, U+205F, U+3000). isBracket likewise exact vs [\[\]\(\),] -> 0 mismatches.
  - Exhaustive small-alphabet sweeps (the place a maximal-munch/backtracking mismatch would live): all strings of length <=6 over {'|',' ','o','r','a'}; length <=5 over {'[',' ','o','r','.',','}; length <=5 over {'.',',',')','\t','|','\xa0','x'}; length <=3 over {'a','|','[',',','o','r',' ','.'} -> 0 mismatches. These directly stress the bracket branch's optional (?:\`s*or`\s)? group and the greedy \s* backtracking, and the delimOr/delimPipe/delimEllipsis fallthrough chain.
  - ~400k + ~250k + ~250k randomized (token-alphabet, realistic-type-field generator over {int,str,bytes,None,List,Dict,Any,float,.mod.Cls,~pkg.Cls} x {' | ','|',' or ',', ','[',']','(',')','...',', ','  |  ','\xa0|\xa0','[ or]',' |','| '}, and dense delimiter-soup) -> 0 mismatches.
  - 120k long dense inputs (length 20-60) over an 18-symbol alphabet incl. non-BMP U+1F600, '\n', U+001C, U+3000 -> 0 mismatches.
  - Boundary corpus: '', ' ', '|', '||', '| |', 'int|str', 'int  |  str', 'int\xa0|\xa0str', 'a | | b', '|...', '...|', '[|]', '(|)', ',|,', '[ or]', '[or]', '[ or', '[ort]', '[ or\tx]', 'a or or b', 'or a', '.', '..', '....', 'a.|.b', 'a...b' -> all agree.
  - Invariant checked on every input: concat of Token.text == input (no character lost/duplicated), and stepLen >= 1 on every nonempty suffix (no model stall) -> never violated, matching stepLen_pos.

PROBED THE 'TOO STRONG' DIRECTION SPECIFICALLY.
  - splitUnionType hardcodes pipeSep = true, i.e. it pins exactly the POST-patch delimiter set. It is not stronger than the patched repo: the pipeSep=false instantiation exists only to build the prepatch rival, and is unreachable from the method contract.
  - The ensures is a total functional equality (out = splitUnionType target) with an EMPTY pre-condition region, so the spec claims agreement on ALL List Char including [] (splitTokens_nil gives [], matching real('') = [] after filter(None,...)). I found no input the spec over-claims on.
  - Boundary honesty audited, not just asserted: make_xref (python.py:285, UNCHANGED by the patch) is handled as an R-refinement at the call boundary rather than an axiom. I read its body and confirmed the '.'/'~' short-name handling (prefix stripping + reftarget rewrite + first-Text replacement) is genuinely DOWNSTREAM of the modeled boundary and byte-identical pre/post-patch, so it carries no discriminating content. mapping.md 2/3.2 and refinement.md A3 disclose this limitation explicitly and correctly (Token.text = the raw re.split piece handed to make_xref, not the rendered node text); this is a scoping choice that is documented, not concealed, and on the F2P field ('int | str') no such prefix occurs so the two coincide. I also confirmed the split_contnode / contnode branch (python.py:314-316) does not alter the piece TEXT or the link/separator classification, only which node object carries it, so it cannot induce a divergence in the modeled (text, linked) projection.

### Corroborating checks
  - Spec region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True -> the pre/post pair share an identical frozen spec signature; the spec was not weakened to admit the rival.
  - scripts/lean_verify.sh Solution.lean -> exit 0, no sorry/admit (only an unused-variable linter warning at 139:5).
  - scripts/lean_verify.sh Solution_prepatch.lean -> FAILS with 'unsolved goals' at 194:34, and the residual goal is precisely the discriminating step (stepLen false / delimLen false vs splitTokens true). The spec has real discriminating power against the pre-patch behavior; it is not vacuous.
  - F2P test (tests/test_domain_py.py::test_info_field_list_piped_type) routes ':type age: int | str' through TypedField.make_xrefs -> the modeled site (docfields.py:186 / python.py:304), and asserts exactly the three-piece stream the model produces: pending_xref 'int', literal_emphasis ' | ', pending_xref 'str'. The modeled boundary is the one the test observes.

CAVEATS (do not change the verdict). (1) An end-to-end run of the real make_xrefs in-process was blocked by an environment incompatibility, not a spec defect: sphinx/util/typing.py:37 does 'from types import Union as types_Union', which fails on the Python 3.10.20 interpreter in the swe-proof env. I compensated with a line-for-line transliteration of python.py:307-326 verified against the repo source, plus the static read of make_xref/docfields callers above; the regex engine used as oracle IS the real CPython re. (2) Testing is exhaustive only for short strings over restricted alphabets and random beyond that, so this is high-confidence agreement, not a proof of equality. No diverging input was found, so per the gate rule I cannot and do not claim a defect.

**CONCLUSION:** FAITHFUL. The modeled function agrees with the real post-patch callee on every input tested (~1.02M, incl. exhaustive Unicode coverage of the two character classes and exhaustive short-string coverage of the munch/backtracking logic), the spec pins exactly the post-patch delimiter set without over-claiming, the one out-of-boundary callee is unchanged by the patch and its exclusion is explicitly disclosed, and the spec is strong enough to reject the pre-patch rival.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE / gold-reconstruction audit of sphinx-doc__sphinx-9258 velvet. No relaxation claimed: meta.json has no `relaxed_leakage` key (checked: `'relaxed_leakage' in meta` = False) and no RELAXED_LEAKAGE.md exists in the bundle, so this is judged as an ordinary leakage review with no inherited disposition.

### WHAT I RAN (my own measurements, not the bundle's assertions):
1. same_spec: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend().language) = True -> the frozen spec region is byte-identical between the gold and pre-image variants; the only divergence is inside impl-start/impl-end (stepLen/delimLen `true` vs `false`), which spec_view elides. Rendered the actual consumer spec_view() and audited THAT text (impl replaced by 'implementation elided', prove_correct body by 'proof elided').
2. scripts/lean_verify.sh on copies in a mktemp -d: Solution.lean exit=0 (only an unused-variable linter warning at:139); Solution_prepatch.lean exit=1 with `error: unsolved goals` at:194 on invariant_1, the goal showing `stepLen false rest` / `delimLen false rest` against `splitTokens true target`. So the discriminator is genuinely load-bearing and the G-DIFF/G-GOLD shape the disposition leans on is sound as measured by me, not just stamped.
3. Gold edit read from the real repo: `git show 06107f838:sphinx/domains/python.py` at base_commit has the PRE-patch `delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\.\.\.)'`; patch.diff adds exactly the `\s*\|\s*` alternative. Confirmed the /tmp worktrees (, `_pzARWe`) are at 06107f838 with gold already applied.

**FACET RE-CONFIRMED:** the ONLY facet the spec view names is the one the public problem_statement requests -- that the vertical bar is a recognized type-field separator, so `bytes | str` / `int | str` splits into two linked references plus one verbatim separator instead of one content run. problem_statement is titled '[RFE] Support union types specification using | (vertical bar/pipe)' and gives `:type text: bytes | str` verbatim. Every spec-view line touching the bar attributes it to that statement: `delimPipe`'s docstring ('The bar is the union-type separator from the problem statement (e.g. `bytes | str`)') and `splitUnionType`'s ('The bar separator is the union-type syntax of the problem statement'). Per instructions I judged against problem_statement only and ignored hints_text (which argues for `or` / `Union[...]` instead -- I did not credit it either way).

NO LEAKING LINE BEYOND THAT FACET (grep over the rendered spec view): the strings `make_xref`, `make_xrefs`, `re.split`, `delims`, `python.py`, `sphinx`, `regex`, `patch`, `diff`, `base_commit`, `9258`, and the regex literal `\s*\|\s*` appear NOWHERE in the spec view. The repo/file/line/symbol bindings and the diff quotation live only in mapping.md and refinement.md, which are auditor artifacts outside the consumer projection (eval/prompts.py feeds only task.spec_view; adapter.spec_view refuses an unelided view). No 'fixed'/'previously'/'no longer'/'used to'/'instead of' pre-vs-post narration in the spec view.

DERIVABILITY OF THE SUB-DETAIL (the one thing I probed hardest -- the whitespace-absorbing shape ` | ` rather than a bare `|`): this is NOT a problem_statement-only-underivable leak, because it follows from the PRE-patch pattern the solver reads at base_commit. Measured on the pre-patch regex: 'int, str' -> [('int',content),(', ',sep),('str',content)] and 'int or str' -> [('int',content),(' or ',sep),('str',content)] -- both existing alternatives already absorb their surrounding whitespace (`\s*[...]\s*`, `\s+or\s+`). So `\s*\|\s*` is the symmetric extension a solver derives from statement + repo context, not a smuggled answer. I also checked the choice is not over-determined by the spec: permuting the pipe alternative's position in the alternation (pipe 3rd vs 4th) gave 0 differing token streams over 200,000 random inputs, so the spec pins no ordering fact the solver could not have picked freely.

SURROUNDING MACHINERY IS PRE-EXISTING CONTEXT, NOT THE EDIT: isBracket (`[] (),`), delimOr (the ` or ` word join), delimEllipsis (`...`), the bracket branch's optional ` or ` infix, isWS's 29-codepoint Unicode whitespace set, and the linked-vs-separator classification all transcribe make_xrefs' behavior AT base_commit, which the solver has in hand. Describing the unchanged context of the function under change does not narrow the fix. The `pipeSep: Bool` parameterization does telegraph that a bar-disabled mode exists (i.e. the feature is currently absent) -- but the statement is an RFE that says exactly that ('Please add a support'), and the consumer view only ever exposes `splitUnionType target = splitTokens true target`, so the flag reveals nothing past the public ask.

BUNDLE-ADDRESSING-THE-PANEL CHECK (reported as its own finding per instructions): NEGATIVE. grep across Solution.lean, refinement.md, mapping.md, meta.json, verdict.md (2620 lines), axiom_check.py, conformance_check.py, properties.py for auditor-directed instruction patterns ('you must/should submit|record|report', 'the honest verdict', 'dear panel/auditor', 'record this as', 'note to the panel', 'attacker') returned nothing. meta.json does carry a prior G-PANEL-3 note whose stored agent_verdict is NO-LEAKAGE, but it is a record of an earlier run, not an instruction to me; I did not rely on it -- the same_spec result, both lean_verify exits, the base_commit regex read, and the whitespace/ordering derivability probes above are my own.

**Verdict:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
