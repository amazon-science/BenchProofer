# P2 adversarial audit — astropy__astropy-14365

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_5b.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8b.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's two `ensures` clauses are exact-equality pins (`out = classify true line`, `out = maskSeq true tokens`) against deep models that I independently re-derived from Solution.lean and diffed against the real callees over 3,000,000 inputs with zero mismatches. The only same-spec attack that VERIFIED (atk_8b, the ungrounded-oracle echo `return maskSeq true tokens`) is extensionally identical to the gold behavior, and its materialized faithful patch RESOLVED under the official harness (F2P + all 8 P2P green). No verify-but-wrong impl exists among 16 attempts.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,8 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK: pre-patch site 1 -- no case folding.
+    return classify false line
     -- impl-end
 
 -- invariants-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -224,7 +224,7 @@
       decreasing i
     do
       let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
+      result := isMarkerTok false t :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,12 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK (partial domain): right everywhere EXCEPT a blank line, which is
+    -- forced to `reject` instead of `comment`.
+    if stripWs line = [] then
+      return LType.reject
+    else
+      return classify true line
     -- impl-end
 
 -- invariants-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,14 +213,13 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
+    -- ATTACK (boundary): loop stops at i = 1, so cell 0's flag is never emitted.
     let mut result : List Bool := []
     let mut i := tokens.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ tokens.length
       invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let t := tokens[i - 1]!
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,19 +213,19 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
+    -- ATTACK (control-flow effect): forward scan appending to the FRONT, so the
+    -- row's flags come out in reverse order.
     let mut result : List Bool := []
-    let mut i := tokens.length
-    while i > 0
+    let mut i := 0
+    while i < tokens.length
       invariant 0 ≤ i ∧ i ≤ tokens.length
-      invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = (maskSeq true (tokens.take i)).reverse
+      done_with i = tokens.length
+      decreasing tokens.length - i
     do
-      let t := tokens[i - 1]!
+      let t := tokens[i]!
       result := isMarkerTok true t :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
```

Attack 6 — `atk_5b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,19 +213,19 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
+    -- ATTACK (control-flow effect): forward scan appending to the FRONT, so the
+    -- row's flags come out in reverse order.
     let mut result : List Bool := []
-    let mut i := tokens.length
-    while i > 0
+    let mut i := 0
+    while i < tokens.length
       invariant 0 ≤ i ∧ i ≤ tokens.length
-      invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = (maskSeq true (tokens.take i)).reverse
+      done_with i = tokens.length
+      decreasing tokens.length - i
     do
-      let t := tokens[i - 1]!
+      let t := tokens[i]!
       result := isMarkerTok true t :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -248,5 +248,6 @@
 
 prove_correct maskFlags by
   loom_solve
-  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
-  simp_all
+  · simp [List.take_succ, maskSeq]
+    simp_all
+  · simp_all
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -224,7 +224,7 @@
       decreasing i
     do
       let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
+      result := isNanTok true t :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,9 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK: fold only the directive, leave marker/nan cells unfolded by
+    -- classifying the *upper-cased* line under the NON-folding recognizer.
+    return classify false (line.map foldChar)
     -- impl-end
 
 -- invariants-start
```

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,20 +213,10 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
-    let mut result : List Bool := []
-    let mut i := tokens.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ tokens.length
-      invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
-      i := i - 1
-    return result
+    -- ATTACK (ungrounded-oracle echo): return the spec function verbatim, with
+    -- no loop at all. Trivially verifies; tests whether the postcondition
+    -- carries real content (i.e. whether `maskSeq true` == the real callee).
+    return maskSeq true tokens
     -- impl-end
 
 /- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
```

Attack 10 — `atk_8b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -213,20 +213,10 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
-    let mut result : List Bool := []
-    let mut i := tokens.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ tokens.length
-      invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
-      i := i - 1
-    return result
+    -- ATTACK (ungrounded-oracle echo): return the spec function verbatim, with
+    -- no loop at all. Trivially verifies; tests whether the postcondition
+    -- carries real content (i.e. whether `maskSeq true` == the real callee).
+    return maskSeq true tokens
     -- impl-end
 
 /- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
@@ -248,5 +238,3 @@
 
 prove_correct maskFlags by
   loom_solve
-  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
-  simp_all
```

Attack 11 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,10 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK (respelling): strip first, then classify. `classify` strips again,
+    -- and stripWs is idempotent, so this should VERIFY -- used to check that a
+    -- verifying-but-differently-spelled impl still refines to a resolving patch.
+    return classify true (stripWs line)
     -- impl-end
 
 -- invariants-start
```

Attack 12 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,13 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK (control-flow reorder): test the directive BEFORE the tail check,
+    -- i.e. accept a directive whose decorative tail spans a line break.
+    let s := stripWs line
+    if isDirective true s then
+      return LType.command
+    else
+      return classify true line
     -- impl-end
 
 -- invariants-start
```

Attack 13 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,20 +213,11 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
-    let mut result : List Bool := []
-    let mut i := tokens.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ tokens.length
-      invariant result = maskSeq true (tokens.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
-      i := i - 1
-    return result
+    -- ATTACK (partial domain / boundary): an empty row yields a spurious flag.
+    if tokens = [] then
+      return [false]
+    else
+      return maskSeq true tokens
     -- impl-end
 
 /- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
@@ -248,5 +239,3 @@
 
 prove_correct maskFlags by
   loom_solve
-  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
-  simp_all
```

Attack 14 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,10 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK (boundary/arity): report the data arity one too high.
+    match classify true line with
+    | LType.data n => return LType.data (n + 1)
+    | other        => return other
     -- impl-end
 
 -- invariants-start
```

Attack 15 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -213,8 +213,7 @@
   ensures out = maskSeq true tokens
   do
     -- impl-start
-    -- Backward scan over the row's cells, deciding the missing-value flag of
-    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
+    -- ATTACK (wrong reserved word): compare each cell against "ON", not "NO".
     let mut result : List Bool := []
     let mut i := tokens.length
     while i > 0
@@ -224,7 +223,7 @@
       decreasing i
     do
       let t := tokens[i - 1]!
-      result := isMarkerTok true t :: result
+      result := eqFold true t "ON".toList :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 16 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -201,9 +201,13 @@
   ensures out = classify true line
   do
     -- impl-start
-    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
-    -- behavior). The recognizer has no internal loop; `line` is read-only.
-    return classify true line
+    -- ATTACK (mixed flag): the reserved verb is matched case-sensitively while
+    -- the data cells fold -- i.e. only HALF of the re.IGNORECASE flag.
+    let s := stripWs line
+    if s ≠ [] && isDirective true s && !isDirective false s then
+      return LType.reject
+    else
+      return classify true line
     -- impl-end
 
 -- invariants-start
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
/- The classification of a single line of this whitespace-delimited scientific
   table format. A line is one of: a blank/decorative line; a header directive;
   a table-break marker; or a data row carrying `n` values. A line meeting none
   of these shapes is rejected. The `fold` flag governs whether the reserved
   words of the format are recognized regardless of letter case (`true`) or only
   in a single canonical case (`false`); the abstract behavior the spec pins is
   the case-insensitive one. This is a deep model of the real recognizer, validated
   == the real callee over >10⁶ inputs by axiom_check.py (G-AX) and
   conformance_check.py (G-CONF). -/
inductive LType where
  | comment  : LType
  | command  : LType
  | newblock : LType
  | data     : Nat → LType
  | reject   : LType
deriving DecidableEq, Repr

/- Whitespace characters this format treats as separators / trim targets. The
   class is the format's full whitespace class, which is not limited to the
   ASCII separators: every code point the tokenizer and the trimmer agree to
   treat as blank is listed. -/
def wsCodes : List Nat :=
  [9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
   133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197, 8198,
   8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Trim leading and trailing whitespace (each line is stripped first). -/
def dropWs : List Char → List Char
  | []      => []
  | c :: cs => if isWs c then dropWs cs else c :: cs

def stripWs (s : List Char) : List Char := dropWs ((dropWs s.reverse).reverse)

/- Split into non-empty whitespace-delimited tokens (the format's tokenizer). -/
def words (s : List Char) : List (List Char) :=
  (s.splitOnP isWs).filter (· ≠ [])

/- The single-character case-folding this format's recognizer uses. It is not
   limited to the ASCII letters: a code point that is a case variant of one of
   the reserved letters folds onto it too (U+017F folds onto `S`). -/
def foldChar (c : Char) : Char :=
  if c.toNat = 383 then 'S' else Char.toUpper c

/- Case-folding equality on character lists: under `fold`, compare with both
   sides folded per character; otherwise compare verbatim. -/
def eqFold (fold : Bool) (a b : List Char) : Bool :=
  if fold then (a.map foldChar) = (b.map foldChar) else a = b

/- The ASCII digits: the class the format's *operand* positions accept. -/
def isDigit (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/- A non-empty run of operand digits. -/
def isDigits (s : List Char) : Bool := s ≠ [] && s.all isDigit

/- The decimal-digit class the format's *numeric literals* accept, given as the
   code-point ranges it covers. It is strictly wider than the ASCII digits:
   every decimal digit, in any script, is admitted in a numeric literal. -/
def digitRanges : List (Nat × Nat) :=
  [(48, 57), (1632, 1641), (1776, 1785), (1984, 1993),
   (2406, 2415), (2534, 2543), (2662, 2671), (2790, 2799),
   (2918, 2927), (3046, 3055), (3174, 3183), (3302, 3311),
   (3430, 3439), (3558, 3567), (3664, 3673), (3792, 3801),
   (3872, 3881), (4160, 4169), (4240, 4249), (6112, 6121),
   (6160, 6169), (6470, 6479), (6608, 6617), (6784, 6793),
   (6800, 6809), (6992, 7001), (7088, 7097), (7232, 7241),
   (7248, 7257), (42528, 42537), (43216, 43225), (43264, 43273),
   (43472, 43481), (43504, 43513), (43600, 43609), (44016, 44025),
   (65296, 65305), (66720, 66729), (68912, 68921), (69734, 69743),
   (69872, 69881), (69942, 69951), (70096, 70105), (70384, 70393),
   (70736, 70745), (70864, 70873), (71248, 71257), (71360, 71369),
   (71472, 71481), (71904, 71913), (72016, 72025), (72784, 72793),
   (73040, 73049), (73120, 73129), (92768, 92777), (93008, 93017),
   (120782, 120831), (123200, 123209), (123632, 123641), (125264, 125273),
   (130032, 130041)]

def isNumDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- The numeric-literal recognizer of the format, as a deterministic automaton
   over `[+-]?(d+(.d*)?|.d+)([eE][+-]?d+)?`, where `d` is the numeric-literal
   digit class (`isNumDigit`, wider than ASCII). State codes:
   0 start, 1 sign, 2 int, 3 dot-after-int, 4 dot-no-int, 5 frac,
   6 e, 7 e-sign, 8 exp, 9 dead. Accepting: {2,3,5,8}. Case-irrelevant. -/
def decStep (st : Nat) (c : Char) : Nat :=
  if st = 0 then
    (if c = '+' || c = '-' then 1 else if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 1 then
    (if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 2 then
    (if isNumDigit c then 2 else if c = '.' then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 3 then
    (if isNumDigit c then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 4 then
    (if isNumDigit c then 5 else 9)
  else if st = 5 then
    (if isNumDigit c then 5 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 6 then
    (if c = '+' || c = '-' then 7 else if isNumDigit c then 8 else 9)
  else if st = 7 then
    (if isNumDigit c then 8 else 9)
  else if st = 8 then
    (if isNumDigit c then 8 else 9)
  else 9

def decRun : Nat → List Char → Nat
  | st, []      => st
  | st, c :: cs => decRun (decStep st c) cs

def isDecimal (s : List Char) : Bool :=
  let f := decRun 0 s
  f = 2 || f = 3 || f = 5 || f = 8

/- The table-break / missing-value marker token of the format. -/
def isMarkerTok (fold : Bool) (t : List Char) : Bool := eqFold fold t "NO".toList

/- The not-a-number sentinel token: an optional sign then the reserved word. -/
def isNanTok (fold : Bool) (t : List Char) : Bool :=
  match t with
  | c :: rest => if c = '+' || c = '-' then eqFold fold rest "nan".toList
                 else eqFold fold t "nan".toList
  | []        => false

/- A single data cell: a numeric literal, the marker, or the not-a-number word. -/
def isDataTok (fold : Bool) (t : List Char) : Bool :=
  isDecimal t || isMarkerTok fold t || isNanTok fold t

/- The header-directive recognizer: the reserved verb, a single literal space,
   one of the two reserved kinds, then one-or-more whitespace-separated integer
   operands (an optional trailing decorative tail is permitted). -/
def isDirective (fold : Bool) (s : List Char) : Bool :=
  eqFold fold (s.take 4) "READ".toList
  && ((s.drop 4).head? = some ' ')
  && (eqFold fold ((s.drop 5).take 4) "SERR".toList
      || eqFold fold ((s.drop 5).take 4) "TERR".toList)
  && (let rest := s.drop 9
      let core := rest.takeWhile (· ≠ '!')
      let ops := words core
      (match core with | c :: _ => isWs c | [] => false)
      && ops ≠ []
      && ops.all isDigits)

/- The decorative tail runs to the end of its own line: it may not span a line
   break. So once a tail is opened, anything beyond the first line break in it
   must itself be blank, or the line as a whole is not accepted. -/
def tailOk (s : List Char) : Bool :=
  let after := (s.dropWhile (· ≠ '!')).drop 1
  let beyond := after.dropWhile (· ≠ '\n')
  beyond.all isWs

/- The full line classifier (see the inductive's doc). Mirrors the recognizer's
   ordered alternation: directive, then break-marker, then data row; a line that
   is only a decorative tail is blank; anything else is rejected. -/
def classify (fold : Bool) (line : List Char) : LType :=
  let s := stripWs line
  if s = [] then LType.comment
  else
    let core := s.takeWhile (· ≠ '!')
    let hasTail := s.any (· = '!')
    let toks := words core
    if hasTail && !tailOk s then LType.reject
    else if isDirective fold s then LType.command
    else if 2 ≤ toks.length && toks.all (isMarkerTok fold) then LType.newblock
    else if toks = [] then (if hasTail then LType.comment else LType.reject)
    else if toks.all (isDataTok fold) then LType.data toks.length
    else LType.reject

/- Per-cell missing-value decision over a row of tokens: a cell is the missing
   sentinel iff its token equals the reserved marker (case-insensitively when
   `fold`). Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern, plan §5.4). -/
def maskSeq (fold : Bool) : List (List Char) → List Bool
  | []      => []
  | t :: ts => isMarkerTok fold t :: maskSeq fold ts

@[grind] lemma maskSeq_nil (fold : Bool) : maskSeq fold [] = [] := rfl
@[grind] lemma maskSeq_cons (fold : Bool) (t : List Char) (ts : List (List Char)) :
    maskSeq fold (t :: ts) = isMarkerTok fold t :: maskSeq fold ts := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method lineType (line : List Char) return (out : LType)
  ensures out = classify true line
  do
    -- impl-start
    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
    -- behavior). The recognizer has no internal loop; `line` is read-only.
    return classify true line
    -- impl-end

-- invariants-start
-- invariants-end

method maskFlags (tokens : List (List Char)) return (out : List Bool)
  ensures out = maskSeq true tokens
  do
    -- impl-start
    -- Backward scan over the row's cells, deciding the missing-value flag of
    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
    let mut result : List Bool := []
    let mut i := tokens.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tokens.length
      invariant result = maskSeq true (tokens.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tokens[i - 1]!
      result := isMarkerTok true t :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
   on the front, so `maskSeq` peels one flag. -/
lemma maskSeq_drop_step (tokens : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tokens.length) :
    maskSeq true (tokens.drop (i - 1))
      = isMarkerTok true tokens[i - 1]! :: maskSeq true (tokens.drop i) := by
  have hlt : i - 1 < tokens.length := by omega
  have hcons : tokens.drop (i - 1) = tokens[i - 1]! :: tokens.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskSeq_cons]

prove_correct lineType by
  loom_solve

prove_correct maskFlags by
  loom_solve
  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** all 16 attacks are byte-identical on spec (same_spec == True for every file, re-confirmed in one final batch; only the impl regions, and where necessary the consumer-supplied prove_correct bodies, were edited). Positive control pos_control.lean (verbatim Solution.lean) verifies, exit 0. Verifications were run concurrently in background batches of <=4 per instructions.

ATTACK LEDGER — cmd: `bash scripts/lean_verify.sh <path>`.
  atk_1  prepatch site 1 (`classify false line`)                        EXIT=1 rejected (PREPATCH REPRODUCED)
  atk_2  prepatch site 2 (`isMarkerTok false` in loop)                  EXIT=1 rejected (PREPATCH REPRODUCED)
  atk_3  partial-domain: blank line forced to `reject`                  EXIT=1 rejected
  atk_4  boundary: loop bound `i > 1`, drops cell 0                     EXIT=1 rejected
  atk_5  control-flow-effect: forward scan, row reversed                EXIT=1 rejected
  atk_5b same, with an honest re-proof attempt (take_succ)              EXIT=1 rejected
  atk_6  wrong predicate: `isNanTok` instead of `isMarkerTok`           EXIT=1 rejected
  atk_7  half-fold: `classify false (line.map foldChar)`                EXIT=1 rejected
  atk_8  oracle echo, stale shipped proof script                        EXIT=1 (proof artifact, not semantics)
  atk_8b oracle echo `return maskSeq true tokens` + adapted proof       EXIT=0 **VERIFIES**
  atk_9  respelling: `classify true (stripWs line)`                     EXIT=1 rejected
  atk_10 control-flow reorder: directive tested BEFORE the tailOk guard EXIT=1 rejected
  atk_11 partial-domain: empty row yields spurious `[false]`            EXIT=1 rejected
  atk_12 boundary/arity: `data n` -> `data (n+1)`                       EXIT=1 rejected
  atk_13 wrong reserved word: cells compared against "ON"               EXIT=1 rejected
  atk_14 mixed flag: verb case-sensitive while cells fold               EXIT=1 rejected

MANDATORY RESOLVE RUN (the one verifying attack): atk_8b's faithful patch is the gold hunk pair (its impl is extensionally the spec function, so the faithful refinement is exactly `re.IGNORECASE` + `v.upper() == "NO"`). Executed `run_resolve('astropy__astropy-14365', <atk_8b.patch>, run_id='geq-atk8b-astropy14365')` -> RESOLVED=True, completed=True, note='resolved', FAIL_TO_PASS success=[test_roundtrip[True]], PASS_TO_PASS 8/8 success, 0 failures. So the verifying attack does NOT break verify=>correct.

INDEPENDENT A-REFERENCE AUDIT (the real work — R/I is G-CONF's). I did NOT trust the shipped axiom_check.py, and found it is in fact a WEAKER model than Solution.lean: its Python `classify` omits the `tailOk` guard entirely and uses only 6 ASCII whitespace chars where Lean's `wsCodes` has 29 (incl. U+0085/U+00A0/U+3000). I therefore wrote diffcheck.py, a line-by-line faithful transliteration of the Lean pure region (full 29-code wsCodes, tailOk, Lean's ASCII-only Char.toUpper, the U+017F->S fold, the 61 isNumDigit ranges, the decStep/decRun DFA), and diffed it against the real `_line_type` dispatch with `_type_re` rebuilt verbatim from qdp.py:62-70:
  - Set-level class equality over all 0x110000 code points: Lean `wsCodes` == Python `str.isspace()` == regex `\s` EXACTLY (0 diffs both directions); Lean `digitRanges` == regex `\d` EXACTLY (0 diffs). The enumerated classes are not approximations.
  - re.IGNORECASE fold-class equality per reserved letter (READSTNOnaeE): for every letter, {c : re.IGNORECASE matches} == {c : foldChar c == foldChar L}. Notably S has class size 3 {0x53,0x73,0x17F} and Lean's special-case `if c.toNat = 383 then 'S'` reproduces it exactly — the one genuinely subtle fidelity point, and it is right.
  - Differential fuzz bigfuzz.py (seed 987654321, unicode-ws/unicode-digit/U+017F/newline-rich alphabet, structured + raw): N=3,000,000 comparisons, classify_bad=0, other_bad=0, for BOTH flag values, plus isDecimal vs re.fullmatch(`_decimal_re`) and the masking predicate.
  Boundary probe (probe1.py) incl. embedded-newline tails, NBSP/ideographic space, Arabic-Indic digits, `READ ſERR 1`: 0 mismatches. atk_10's rejection independently confirms the `tailOk` guard carries real proof force (it is load-bearing, not decoration).

**REFINEMENT.MD LEG AUDIT:** every leg is R, A-reference, or I; no kind-3. meta.json `axioms` == [] and there is genuinely no `-- axioms-start` content, so there are no A-consumed legs and no axiom-soundness liability — the claim in refinement.md §C checks out. All cited line numbers verified against qdp.py at base_commit 7269fa3e (`:71` re.compile, `:309` `if v == "NO"`, `:62` `_decimal_re`, `:63` `_command_re`, `:83` data label, `:307-308` value loop — all 8/8 accurate). A2/B2 correspondence (fold == the re.IGNORECASE flag; fold == `.upper()`) is exactly what my independent fuzz confirms. Both prepatch variants diverge only at the discriminating clause (diffed) and both are re-encoded here as atk_1/atk_2, both rejected. Shipped gates re-run green: axiom_check.py exit 0 (1.2e6 lines / 6e5 tokens / 4.4e5 cells), conformance_check.py exit 0 (200000 inputs, seed 14365, 0 disagreements).

STRONGEST RESIDUAL CRITICISM, TESTED NOT SPECULATED: mapping.md §2 explicitly scopes the model to `delimiter=None`, so the frozen spec pins nothing about the `delimiter=','` path — yet P2P contains test_roundtrip_example_comma, and the gold patch's two hunks are delimiter-agnostic. A faithful-but-scope-minimal refinement could therefore fix only the whitespace path. I materialized exactly that adversarial patch (atk_scoped.patch: `re.IGNORECASE if delimiter is None else 0` and a delimiter-conditional masking test) and RAN it: `run_resolve(..., run_id='geq-scoped-astropy14365')` -> RESOLVED=True, F2P success, PASS_TO_PASS 8/8 including test_roundtrip_example_comma. So the scoping gap is real in the documentation but empirically not a resolve hole — the comma test's data is upper-case, so nothing in the suite distinguishes the scoped fix. Documentation nit only, not a G-EQ failure.

**ARTIFACT COMPLETENESS:** re-confirmed at the end of the audit that same_spec==True holds for all 16 attacks and the positive control, and that every submitted path is present and current.

**VERDICT SOUND:** 16 attacks run (>=5 required) across partial-domain, boundary, control-flow-effect, wrong-predicate, mixed-flag and ungrounded-oracle-echo classes; 15 correctly rejected; the single verifier is extensionally the gold behavior and its materialized faithful patch RESOLVED under the official harness. Both executed resolve runs resolved. No verify=/=>correct counterexample found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_5b.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8b.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's two `ensures` clauses are exact-equality pins (`out = classify true line`, `out = maskSeq true tokens`) against deep models that I independently re-derived from Solution.lean and diffed against the real callees over 3,000,000 inputs with zero mismatches. The only same-spec attack that VERIFIED (atk_8b, the ungrounded-oracle echo `return maskSeq true tokens`) is extensionally identical to the gold behavior, and its materialized faithful patch RESOLVED under the official harness (F2P + all 8 P2P green). No verify-but-wrong impl exists among 16 attempts.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5b.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_8b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_14.lean` → rejected (same spec, does not verify — good)

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
/- The classification of a single line of this whitespace-delimited scientific
   table format. A line is one of: a blank/decorative line; a header directive;
   a table-break marker; or a data row carrying `n` values. A line meeting none
   of these shapes is rejected. The `fold` flag governs whether the reserved
   words of the format are recognized regardless of letter case (`true`) or only
   in a single canonical case (`false`); the abstract behavior the spec pins is
   the case-insensitive one. This is a deep model of the real recognizer, validated
   == the real callee over >10⁶ inputs by axiom_check.py (G-AX) and
   conformance_check.py (G-CONF). -/
inductive LType where
  | comment  : LType
  | command  : LType
  | newblock : LType
  | data     : Nat → LType
  | reject   : LType
deriving DecidableEq, Repr

/- Whitespace characters this format treats as separators / trim targets. The
   class is the format's full whitespace class, which is not limited to the
   ASCII separators: every code point the tokenizer and the trimmer agree to
   treat as blank is listed. -/
def wsCodes : List Nat :=
  [9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
   133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197, 8198,
   8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Trim leading and trailing whitespace (each line is stripped first). -/
def dropWs : List Char → List Char
  | []      => []
  | c :: cs => if isWs c then dropWs cs else c :: cs

def stripWs (s : List Char) : List Char := dropWs ((dropWs s.reverse).reverse)

/- Split into non-empty whitespace-delimited tokens (the format's tokenizer). -/
def words (s : List Char) : List (List Char) :=
  (s.splitOnP isWs).filter (· ≠ [])

/- The single-character case-folding this format's recognizer uses. It is not
   limited to the ASCII letters: a code point that is a case variant of one of
   the reserved letters folds onto it too (U+017F folds onto `S`). -/
def foldChar (c : Char) : Char :=
  if c.toNat = 383 then 'S' else Char.toUpper c

/- Case-folding equality on character lists: under `fold`, compare with both
   sides folded per character; otherwise compare verbatim. -/
def eqFold (fold : Bool) (a b : List Char) : Bool :=
  if fold then (a.map foldChar) = (b.map foldChar) else a = b

/- The ASCII digits: the class the format's *operand* positions accept. -/
def isDigit (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/- A non-empty run of operand digits. -/
def isDigits (s : List Char) : Bool := s ≠ [] && s.all isDigit

/- The decimal-digit class the format's *numeric literals* accept, given as the
   code-point ranges it covers. It is strictly wider than the ASCII digits:
   every decimal digit, in any script, is admitted in a numeric literal. -/
def digitRanges : List (Nat × Nat) :=
  [(48, 57), (1632, 1641), (1776, 1785), (1984, 1993),
   (2406, 2415), (2534, 2543), (2662, 2671), (2790, 2799),
   (2918, 2927), (3046, 3055), (3174, 3183), (3302, 3311),
   (3430, 3439), (3558, 3567), (3664, 3673), (3792, 3801),
   (3872, 3881), (4160, 4169), (4240, 4249), (6112, 6121),
   (6160, 6169), (6470, 6479), (6608, 6617), (6784, 6793),
   (6800, 6809), (6992, 7001), (7088, 7097), (7232, 7241),
   (7248, 7257), (42528, 42537), (43216, 43225), (43264, 43273),
   (43472, 43481), (43504, 43513), (43600, 43609), (44016, 44025),
   (65296, 65305), (66720, 66729), (68912, 68921), (69734, 69743),
   (69872, 69881), (69942, 69951), (70096, 70105), (70384, 70393),
   (70736, 70745), (70864, 70873), (71248, 71257), (71360, 71369),
   (71472, 71481), (71904, 71913), (72016, 72025), (72784, 72793),
   (73040, 73049), (73120, 73129), (92768, 92777), (93008, 93017),
   (120782, 120831), (123200, 123209), (123632, 123641), (125264, 125273),
   (130032, 130041)]

def isNumDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- The numeric-literal recognizer of the format, as a deterministic automaton
   over `[+-]?(d+(.d*)?|.d+)([eE][+-]?d+)?`, where `d` is the numeric-literal
   digit class (`isNumDigit`, wider than ASCII). State codes:
   0 start, 1 sign, 2 int, 3 dot-after-int, 4 dot-no-int, 5 frac,
   6 e, 7 e-sign, 8 exp, 9 dead. Accepting: {2,3,5,8}. Case-irrelevant. -/
def decStep (st : Nat) (c : Char) : Nat :=
  if st = 0 then
    (if c = '+' || c = '-' then 1 else if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 1 then
    (if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 2 then
    (if isNumDigit c then 2 else if c = '.' then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 3 then
    (if isNumDigit c then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 4 then
    (if isNumDigit c then 5 else 9)
  else if st = 5 then
    (if isNumDigit c then 5 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 6 then
    (if c = '+' || c = '-' then 7 else if isNumDigit c then 8 else 9)
  else if st = 7 then
    (if isNumDigit c then 8 else 9)
  else if st = 8 then
    (if isNumDigit c then 8 else 9)
  else 9

def decRun : Nat → List Char → Nat
  | st, []      => st
  | st, c :: cs => decRun (decStep st c) cs

def isDecimal (s : List Char) : Bool :=
  let f := decRun 0 s
  f = 2 || f = 3 || f = 5 || f = 8

/- The table-break / missing-value marker token of the format. -/
def isMarkerTok (fold : Bool) (t : List Char) : Bool := eqFold fold t "NO".toList

/- The not-a-number sentinel token: an optional sign then the reserved word. -/
def isNanTok (fold : Bool) (t : List Char) : Bool :=
  match t with
  | c :: rest => if c = '+' || c = '-' then eqFold fold rest "nan".toList
                 else eqFold fold t "nan".toList
  | []        => false

/- A single data cell: a numeric literal, the marker, or the not-a-number word. -/
def isDataTok (fold : Bool) (t : List Char) : Bool :=
  isDecimal t || isMarkerTok fold t || isNanTok fold t

/- The header-directive recognizer: the reserved verb, a single literal space,
   one of the two reserved kinds, then one-or-more whitespace-separated integer
   operands (an optional trailing decorative tail is permitted). -/
def isDirective (fold : Bool) (s : List Char) : Bool :=
  eqFold fold (s.take 4) "READ".toList
  && ((s.drop 4).head? = some ' ')
  && (eqFold fold ((s.drop 5).take 4) "SERR".toList
      || eqFold fold ((s.drop 5).take 4) "TERR".toList)
  && (let rest := s.drop 9
      let core := rest.takeWhile (· ≠ '!')
      let ops := words core
      (match core with | c :: _ => isWs c | [] => false)
      && ops ≠ []
      && ops.all isDigits)

/- The decorative tail runs to the end of its own line: it may not span a line
   break. So once a tail is opened, anything beyond the first line break in it
   must itself be blank, or the line as a whole is not accepted. -/
def tailOk (s : List Char) : Bool :=
  let after := (s.dropWhile (· ≠ '!')).drop 1
  let beyond := after.dropWhile (· ≠ '\n')
  beyond.all isWs

/- The full line classifier (see the inductive's doc). Mirrors the recognizer's
   ordered alternation: directive, then break-marker, then data row; a line that
   is only a decorative tail is blank; anything else is rejected. -/
def classify (fold : Bool) (line : List Char) : LType :=
  let s := stripWs line
  if s = [] then LType.comment
  else
    let core := s.takeWhile (· ≠ '!')
    let hasTail := s.any (· = '!')
    let toks := words core
    if hasTail && !tailOk s then LType.reject
    else if isDirective fold s then LType.command
    else if 2 ≤ toks.length && toks.all (isMarkerTok fold) then LType.newblock
    else if toks = [] then (if hasTail then LType.comment else LType.reject)
    else if toks.all (isDataTok fold) then LType.data toks.length
    else LType.reject

/- Per-cell missing-value decision over a row of tokens: a cell is the missing
   sentinel iff its token equals the reserved marker (case-insensitively when
   `fold`). Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern, plan §5.4). -/
def maskSeq (fold : Bool) : List (List Char) → List Bool
  | []      => []
  | t :: ts => isMarkerTok fold t :: maskSeq fold ts

@[grind] lemma maskSeq_nil (fold : Bool) : maskSeq fold [] = [] := rfl
@[grind] lemma maskSeq_cons (fold : Bool) (t : List Char) (ts : List (List Char)) :
    maskSeq fold (t :: ts) = isMarkerTok fold t :: maskSeq fold ts := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method lineType (line : List Char) return (out : LType)
  ensures out = classify true line
  do
    -- impl-start
    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
    -- behavior). The recognizer has no internal loop; `line` is read-only.
    return classify true line
    -- impl-end

-- invariants-start
-- invariants-end

method maskFlags (tokens : List (List Char)) return (out : List Bool)
  ensures out = maskSeq true tokens
  do
    -- impl-start
    -- Backward scan over the row's cells, deciding the missing-value flag of
    -- each with case-folding ENABLED. `tokens` is read-only (not mutated).
    let mut result : List Bool := []
    let mut i := tokens.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tokens.length
      invariant result = maskSeq true (tokens.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tokens[i - 1]!
      result := isMarkerTok true t :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
   on the front, so `maskSeq` peels one flag. -/
lemma maskSeq_drop_step (tokens : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tokens.length) :
    maskSeq true (tokens.drop (i - 1))
      = isMarkerTok true tokens[i - 1]! :: maskSeq true (tokens.drop i) := by
  have hlt : i - 1 < tokens.length := by omega
  have hcons : tokens.drop (i - 1) = tokens[i - 1]! :: tokens.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskSeq_cons]

prove_correct lineType by
  loom_solve

prove_correct maskFlags by
  loom_solve
  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** all 16 attacks are byte-identical on spec (same_spec == True for every file, re-confirmed in one final batch; only the impl regions, and where necessary the consumer-supplied prove_correct bodies, were edited). Positive control pos_control.lean (verbatim Solution.lean) verifies, exit 0. Verifications were run concurrently in background batches of <=4 per instructions.

ATTACK LEDGER — cmd: `bash scripts/lean_verify.sh <path>`.
  atk_1  prepatch site 1 (`classify false line`)                        EXIT=1 rejected (PREPATCH REPRODUCED)
  atk_2  prepatch site 2 (`isMarkerTok false` in loop)                  EXIT=1 rejected (PREPATCH REPRODUCED)
  atk_3  partial-domain: blank line forced to `reject`                  EXIT=1 rejected
  atk_4  boundary: loop bound `i > 1`, drops cell 0                     EXIT=1 rejected
  atk_5  control-flow-effect: forward scan, row reversed                EXIT=1 rejected
  atk_5b same, with an honest re-proof attempt (take_succ)              EXIT=1 rejected
  atk_6  wrong predicate: `isNanTok` instead of `isMarkerTok`           EXIT=1 rejected
  atk_7  half-fold: `classify false (line.map foldChar)`                EXIT=1 rejected
  atk_8  oracle echo, stale shipped proof script                        EXIT=1 (proof artifact, not semantics)
  atk_8b oracle echo `return maskSeq true tokens` + adapted proof       EXIT=0 **VERIFIES**
  atk_9  respelling: `classify true (stripWs line)`                     EXIT=1 rejected
  atk_10 control-flow reorder: directive tested BEFORE the tailOk guard EXIT=1 rejected
  atk_11 partial-domain: empty row yields spurious `[false]`            EXIT=1 rejected
  atk_12 boundary/arity: `data n` -> `data (n+1)`                       EXIT=1 rejected
  atk_13 wrong reserved word: cells compared against "ON"               EXIT=1 rejected
  atk_14 mixed flag: verb case-sensitive while cells fold               EXIT=1 rejected

MANDATORY RESOLVE RUN (the one verifying attack): atk_8b's faithful patch is the gold hunk pair (its impl is extensionally the spec function, so the faithful refinement is exactly `re.IGNORECASE` + `v.upper() == "NO"`). Executed `run_resolve('astropy__astropy-14365', <atk_8b.patch>, run_id='geq-atk8b-astropy14365')` -> RESOLVED=True, completed=True, note='resolved', FAIL_TO_PASS success=[test_roundtrip[True]], PASS_TO_PASS 8/8 success, 0 failures. So the verifying attack does NOT break verify=>correct.

INDEPENDENT A-REFERENCE AUDIT (the real work — R/I is G-CONF's). I did NOT trust the shipped axiom_check.py, and found it is in fact a WEAKER model than Solution.lean: its Python `classify` omits the `tailOk` guard entirely and uses only 6 ASCII whitespace chars where Lean's `wsCodes` has 29 (incl. U+0085/U+00A0/U+3000). I therefore wrote diffcheck.py, a line-by-line faithful transliteration of the Lean pure region (full 29-code wsCodes, tailOk, Lean's ASCII-only Char.toUpper, the U+017F->S fold, the 61 isNumDigit ranges, the decStep/decRun DFA), and diffed it against the real `_line_type` dispatch with `_type_re` rebuilt verbatim from qdp.py:62-70:
  - Set-level class equality over all 0x110000 code points: Lean `wsCodes` == Python `str.isspace()` == regex `\s` EXACTLY (0 diffs both directions); Lean `digitRanges` == regex `\d` EXACTLY (0 diffs). The enumerated classes are not approximations.
  - re.IGNORECASE fold-class equality per reserved letter (READSTNOnaeE): for every letter, {c : re.IGNORECASE matches} == {c : foldChar c == foldChar L}. Notably S has class size 3 {0x53,0x73,0x17F} and Lean's special-case `if c.toNat = 383 then 'S'` reproduces it exactly — the one genuinely subtle fidelity point, and it is right.
  - Differential fuzz bigfuzz.py (seed 987654321, unicode-ws/unicode-digit/U+017F/newline-rich alphabet, structured + raw): N=3,000,000 comparisons, classify_bad=0, other_bad=0, for BOTH flag values, plus isDecimal vs re.fullmatch(`_decimal_re`) and the masking predicate.
  Boundary probe (probe1.py) incl. embedded-newline tails, NBSP/ideographic space, Arabic-Indic digits, `READ ſERR 1`: 0 mismatches. atk_10's rejection independently confirms the `tailOk` guard carries real proof force (it is load-bearing, not decoration).

**REFINEMENT.MD LEG AUDIT:** every leg is R, A-reference, or I; no kind-3. meta.json `axioms` == [] and there is genuinely no `-- axioms-start` content, so there are no A-consumed legs and no axiom-soundness liability — the claim in refinement.md §C checks out. All cited line numbers verified against qdp.py at base_commit 7269fa3e (`:71` re.compile, `:309` `if v == "NO"`, `:62` `_decimal_re`, `:63` `_command_re`, `:83` data label, `:307-308` value loop — all 8/8 accurate). A2/B2 correspondence (fold == the re.IGNORECASE flag; fold == `.upper()`) is exactly what my independent fuzz confirms. Both prepatch variants diverge only at the discriminating clause (diffed) and both are re-encoded here as atk_1/atk_2, both rejected. Shipped gates re-run green: axiom_check.py exit 0 (1.2e6 lines / 6e5 tokens / 4.4e5 cells), conformance_check.py exit 0 (200000 inputs, seed 14365, 0 disagreements).

STRONGEST RESIDUAL CRITICISM, TESTED NOT SPECULATED: mapping.md §2 explicitly scopes the model to `delimiter=None`, so the frozen spec pins nothing about the `delimiter=','` path — yet P2P contains test_roundtrip_example_comma, and the gold patch's two hunks are delimiter-agnostic. A faithful-but-scope-minimal refinement could therefore fix only the whitespace path. I materialized exactly that adversarial patch (atk_scoped.patch: `re.IGNORECASE if delimiter is None else 0` and a delimiter-conditional masking test) and RAN it: `run_resolve(..., run_id='geq-scoped-astropy14365')` -> RESOLVED=True, F2P success, PASS_TO_PASS 8/8 including test_roundtrip_example_comma. So the scoping gap is real in the documentation but empirically not a resolve hole — the comma test's data is upper-case, so nothing in the suite distinguishes the scoped fix. Documentation nit only, not a G-EQ failure.

**ARTIFACT COMPLETENESS:** re-confirmed at the end of the audit that same_spec==True holds for all 16 attacks and the positive control, and that every submitted path is present and current.

**VERDICT SOUND:** 16 attacks run (>=5 required) across partial-domain, boundary, control-flow-effect, wrong-predicate, mixed-flag and ungrounded-oracle-echo classes; 15 correctly rejected; the single verifier is extensionally the gold behavior and its materialized faithful patch RESOLVED under the official harness. Both executed resolve runs resolved. No verify=/=>correct counterexample found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK SUMMARY — I attempted to break faithfulness (spec too strong / drifts from real repo behavior) and FAILED to find any diverging input across ~2.5M differential trials.

### METHODOLOGY (independent, not reusing bundle's axiom_check.py/conformance_check.py):
1. Created my own worktree at base_commit 7269fa3e33e8d02485a647da91a5a2a60a06af61.
2. Wrote my OWN literal transliteration of Solution.lean's pure region to Python (spec.py), including Lean's exact dropWs/stripWs/words/splitOnP/takeWhile/drop semantics.
3. Built the oracle two ways to remove hand-transcription as a confound: my own rebuild of `_type_re`, and (b) realrepo.py which exec's the GENUINE `_line_type` source text sliced verbatim out of the worktree file, with a re.compile shim injecting/omitting re.IGNORECASE. The shim reproduces all `_line_type` docstring examples exactly. Both flags (fold=true/false) tested on every input, so pre- AND post-patch behavior are both pinned.

### CHECKS THAT PASSED (attacks that found nothing):
- wsCodes (29 entries) == exactly {i : re.match(r'\s\Z', chr(i))} == exactly {i : chr(i).strip()==''} over the full 0..0x10FFFF range. Both the regex \s class and str.strip() agree, so the single wsCodes list correctly serves both the tokenizer and the trimmer. No drift.
- digitRanges (650 code points, 61 ranges) == exactly {i : re.match(r'\d\Z', chr(i))} over full Unicode. Zero symmetric difference. The claim that numeric literals admit any-script decimals is exactly right.
- foldChar: verified by Lean #eval that Char.toUpper is ASCII-only (383->383, 0xE0->0xE0, 0x131->0x131, 0x17F->0x17F, 0xDF->0xDF). Then enumerated, per reserved letter, every code point re.IGNORECASE deems equal: R/E/A/D/N/O/T are ASCII-pair-only; S additionally matches U+017F; [TS] = {S,T,s,t,U+017F}; [eE] = {E,e}. The spec's special-case 'if c.toNat = 383 then S' is precisely the one non-ASCII fold re.IGNORECASE performs on this pattern's letters. Neither too strong nor too weak.
- Site 2 attack on Python .upper() being full-Unicode (can expand length) vs spec's per-char foldChar: enumerated all 0x110000 code points for upper()=='N'/'O'/'NO'/''; only ASCII pairs map to N and O, nothing uppercases to the 2-char 'NO', no code point uppercases to ''. Of the 102 length-expanding uppercases only U+0149 ('ŉ'->'ʼN') touches N/O and cannot form 'NO'. Then verified isMarkerTok(true,t) == (t.upper()=='NO') and isMarkerTok(false,t) == (t=='NO') over t in {c, 'N'+c, c+'O', c+c} for ALL 0x110000 code points c: zero mismatches.
- words vs Python str.split(): 300k fuzz + exhaustive to length 5 over {a,space,tab,U+00A0,U+3000,U+001C,newline} (19,608 strings). Zero mismatches, confirming the mapping.md delimiter=None bijection.
- classify vs genuine repo `_line_type`, BOTH flags: 58 hand-picked boundary cases (incl. all docstring examples, lower-case directives, 'READSERR 1', 'READ  SERR 1', U+017F variants, split tails '!a\nb', '1e', '.', '1..2'); 800k structured/char fuzz vs my regex rebuild; 800k vs the genuine repo function; 900k tail/whitespace/newline-heavy fuzz; and EXHAUSTIVE enumeration: 55,987 over {N,O,n,!,newline,space}^<=6; 137,257 over {1,.,e,-,+,!,space}^<=6; 111,111 over {R,E,A,D,S,T,1,space,!}^<=5; 19,608 over {n,a,N,space,O,1,!}^<=5; 37,449 over {!,newline,CR,space,1,x,U+00A0,VT}^<=5; plus 66,429 directive-prefixed, 18,724 marker-prefixed, 9,425 data-prefixed suffix enumerations. ALL ZERO MISMATCHES.
- Targeted ASCII-vs-Unicode-digit asymmetry attack (the most promising drift vector: `_command_re` operands are [0-9] ASCII while `_decimal_re` uses Unicode-wide \d; the spec correspondingly uses isDigit for isDirective operands but isNumDigit in decStep): 144 crafted cases over 9 non-ASCII digit scripts. Zero mismatches — the spec's split of the two digit classes is faithful, not an over-approximation.
- The subtle tailOk clause (regex '.' does not match newline, so a tail containing a line break must have blank remainder) was specifically hammered by the tail-cr exhaustive run and gen3 fuzz. Faithful.

### Bundle integrity
- Solution.lean elaborates clean under scripts/lean_verify.sh (exit 0, no sorry/admit).
- same_spec(Solution, Solution_prepatch) = True and same_spec(Solution, Solution_prepatch_2) = True via markers.same_spec with the velvet backend: spec region is byte-identical, so the prepatch variants are legitimate G-DIFF witnesses and not spec edits.
- Both prepatch variants FAIL to verify with 'unsolved goals' (prepatch:248:23 = site 1 classify false; prepatch_2:252:24 = site 2 isMarkerTok false), matching refinement.md's G-DIFF claims exactly.
- patch.diff is the gold patch verbatim and both hunks (re.IGNORECASE at qdp.py:71, v.upper()=='NO' at qdp.py:309) correspond to the fold=true legs of classify and maskSeq respectively, which are exactly what the two ensures clauses pin.

### RESIDUAL SCOPE CAVEATS (honestly disclosed, but NOT faithfulness defects — they are declared scoping in mapping.md §2, not undisclosed drift):
- The model fixes delimiter=None. The delimiter=',' path is genuinely unchanged by the patch and off the F2P path, so this is legitimate scoping, disclosed in mapping.md. I did not fuzz it.
- Site 2 is modeled as the per-cell boolean only; the downstream int()/float() parse (and its exception behavior on a non-numeric non-NO cell) is outside the spec. This is sound because the patch does not touch that parse, and classify already gates which lines reach it.
- maskFlags's precondition-free signature accepts token lists that classify would never produce; this makes the spec WEAKER-scoped, not stronger, so it cannot be a faithfulness break.

**CONCLUSION:** no diverging input found. The two deep models are unusually tight — the wsCodes and digitRanges lists are exact Unicode-complete matches, and the U+017F fold special case shows the author actually enumerated re.IGNORECASE's behavior rather than assuming ASCII. I could not make the spec disagree with the real callee on any input. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** INDEPENDENTLY RE-DERIVED (not a rubber-stamp of the recorded pass). Method: rebuilt the spec view myself from markers.spec_view(VelvetBackend) rather than trusting meta.

1. SPEC-REGION BYTE-IDENTITY (required check): CONFIRMED. same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True. Stronger than required: the three spec views are BYTE-identical, sha256 b675991d31de038c... for all three, which also matches meta gates.G-HYGIENE.data.region_hashes.spec_view exactly. So no prepatch smuggles a spec change.

2. CORE SOUNDNESS (so the disposition rests on solid ground): Solution.lean verifies via scripts/lean_verify.sh, EXIT=0, no sorry. Both prepatches genuinely FAIL (EXIT=1 each) against that identical spec -> G-DIFF is real, one failing prepatch per gold hunk.

3. MECHANICAL SCREEN re-run from source (leakage.screen with the frozen row): PASSED, hard_failures=[]. Gold changed_symbols={line_type, get_tables_from_qdp_file}, changed_files=[astropy/io/ascii/qdp.py], 4 changed lines -- none reproduced, no diff markers, no file/module path.

4. MY OWN ADVERSARIAL SCANS (beyond the gate):
   - Mechanism tells ALL ABSENT from the spec view: IGNORECASE, ignorecase, re.compile, 're.', regex, flag-as-regex-flag, numpy, np.ma, masked, qdp, QDP, astropy, `_line_type`, line_type, `_get_tables`, '.upper', 'upper()'. The only 'flag'/'import' hits are benign ('the `fold` flag', 'import Velvet.Std').
   - Narration ALL ABSENT: bug/fix/patch/wrong/broken/previously/incorrect/regression/crash/error/fail/raise/ValueError.
   - Gold-vocabulary sweep: only generic English/Lean tokens collide (data, else, nan, comment, values, number, split, return, def, None) -- no edit-localizing token.
   - TEST-LEAK scan (my addition; the velvet flavor's screen ignores test_patch): lowercase_header, lowercase, test_roundtrip, parametrize, roundtrip, test_qdp ALL absent. The hidden F2P test's identity is not disclosed.
   - PRIVATE-TOKEN echo test (my strongest probe): tokens present in gold+hints_text+test_patch but absent from {problem_statement UNION the pre-patch qdp.py the solver already has}. Only hits: 'anything', 'every', 'false', 'insensitive' -- three are ordinary English/Lean, and 'insensitive' is the PUBLIC concept (PS says verbatim 'QDP itself is not case sensitive'). No private echo.

5. THE SUBSTANTIVE QUESTION -- does pinning `fold=true` leak? NO. The public problem_statement already discloses the ENTIRE fix intent, verbatim: title 'ascii.qdp Table format assumes QDP commands are upper case'; 'QDP itself is not case sensitive and case use "read serr 1 2"'; 'the expectation that all commands be all-caps should be removed'; plus the reproducer and 'Unrecognized QDP line'. The spec pins `out = classify true line` / `out = maskSeq true tokens` -- i.e. case-insensitive recognition, precisely the behavior the public issue DEMANDS. It discloses neither the LOCATION nor the MECHANISM (no re.IGNORECASE, no .upper(), no line numbers, no symbols).

6. SITE 2 IS NOT A HINTS-ONLY SECOND FACET (checked, because that is the usual RELAXED_LEAKAGE trigger -- cf. astropy-14598, django-11141). Site 2 masks lower-case 'no' cells. That follows DIRECTLY from the public 'QDP itself is not case sensitive' applied to the format's missing-value sentinel, and 'NO' is documented in the pre-patch qdp.py docstrings the solver holds. Notably the hints_text contains NOTHING about the NO-masking hunk (it only says the regex is not case insensitive) -- so site 2 is strictly MORE public-derivable than hints-derivable. No hints-only discriminator exists here, hence correctly NOT a relaxed-leakage instance (meta.relaxed_leakage is unset, no RELAXED_LEAKAGE.md -- the right disposition).

7. Identifiers are abstract and format-neutral (LType, classify, fold, isMarkerTok, maskSeq, lineType, maskFlags, eqFold, foldChar); comments describe 'this whitespace-delimited scientific table format' without naming QDP/astropy. Consistent with the naming convention across the other velvet bundles.

**CONCLUSION:** the spec view reveals nothing about the gold edit beyond what the public problem_statement already states. A faithful spec must pin the corrected behavior, and doing exactly that -- and no more -- is not leakage. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.