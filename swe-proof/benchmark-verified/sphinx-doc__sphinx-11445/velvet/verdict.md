# P2 adversarial audit — sphinx-doc__sphinx-11445

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, verifying, behaviorally-WRONG impl exists whose faithful refined patch fails to resolve. The postcondition `pos = leadingMetadata content` is a TOTAL functional equality to a fully-concrete pure fold, so any terminating verifying impl computes exactly the correct count. The only verifying attack (atk_8, `return leadingMetadata content`) is behaviorally CORRECT; its faithful refined patch = the gold patch, which RESOLVED=True COMPLETED=True. The only OTHER verifying construct is atk_9 (`while True` partial-correctness vacuity), which is postcondition-INDEPENDENT (probe_falsedone verifies with a literally-false `done_with (... ∧ 0=1)`) and whose faithful infinite-loop patch does NOT complete (COMPLETED=False → inconclusive class per build_one.py:306-312, NOT a `completed ∧ ¬resolved` break). It is the sanctioned `termination "partial"` escape hatch (spec_guide §1.1), uniform across all partial-correctness bundles, not a weakness of this spec.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -102,21 +102,9 @@
   ensures pos = leadingMetadata content
   do
     -- impl-start
-    let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
-      invariant i ≤ content.length
-      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
-      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
-    do
-      i := i + 1
-    return i
+    let _ := content
+    return 0
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
   loom_solve
-  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
-      at invariant_2
-    omega
-  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
-    omega
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -102,21 +102,8 @@
   ensures pos = leadingMetadata content
   do
     -- impl-start
-    let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
-      invariant i ≤ content.length
-      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
-      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
-    do
-      i := i + 1
-    return i
+    return content.length
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
   loom_solve
-  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
-      at invariant_2
-    omega
-  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
-    omega
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -107,10 +107,9 @@
       invariant i ≤ content.length
       invariant leadingMetadata content = i + leadingMetadata (content.drop i)
       done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
     do
       i := i + 1
-    return i
+    return i + 1
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -102,12 +102,17 @@
   ensures pos = leadingMetadata content
   do
     -- impl-start
+    let looseMetadataLine : List Char → Bool := fun line =>
+      match line with
+      | ':' :: rest =>
+          let word := rest.takeWhile (fun c => c.isAlpha || c.isDigit || c = '_')
+          !word.isEmpty && ((rest.drop word.length).headD ' ' == ':')
+      | _ => false
     let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
+    while i < content.length ∧ looseMetadataLine content[i]!
       invariant i ≤ content.length
       invariant leadingMetadata content = i + leadingMetadata (content.drop i)
       done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
     do
       i := i + 1
     return i
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -102,21 +102,8 @@
   ensures pos = leadingMetadata content
   do
     -- impl-start
-    let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
-      invariant i ≤ content.length
-      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
-      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
-    do
-      i := i + 1
-    return i
+    return (content.filter isMetadataLine).length
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
   loom_solve
-  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
-      at invariant_2
-    omega
-  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
-    omega
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -103,11 +103,10 @@
   do
     -- impl-start
     let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
+    while i + 1 < content.length ∧ isMetadataLine content[i]!
       invariant i ≤ content.length
       invariant leadingMetadata content = i + leadingMetadata (content.drop i)
       done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
     do
       i := i + 1
     return i
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -103,20 +103,13 @@
   do
     -- impl-start
     let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
-      invariant i ≤ content.length
-      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
+    while True
+      invariant True
       done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
     do
-      i := i + 1
+      i := i
     return i
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
   loom_solve
-  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
-      at invariant_2
-    omega
-  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
-    omega
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- axioms-end
@@ -102,21 +102,8 @@
   ensures pos = leadingMetadata content
   do
     -- impl-start
-    let mut i := 0
-    while i < content.length ∧ isMetadataLine content[i]!
-      invariant i ≤ content.length
-      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
-      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
-      decreasing content.length - i
-    do
-      i := i + 1
-    return i
+    return leadingMetadata content
     -- impl-end
 
 prove_correct countLeadingMetadataLines by
   loom_solve
-  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
-      at invariant_2
-    omega
-  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
-    omega
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Whether a single text line is recognised by the strict line-classifier this
   module relies on (a standard reStructuredText line-classification grammar).

   A line is classified when it begins with ':' immediately followed by a
   character that is neither ':' nor a space, and then — scanning forward over
   the remaining characters — a ':' is reached that is *terminated* (it is the
   last character, or the next character is a space) while the character just
   before that closing ':' is not a space. A ':' that is immediately followed by
   a backtick does NOT terminate the marker (so an inline cross-reference such
   as `:role:` followed by a backtick is rejected). A backslash escapes the
   following character (the escaped character cannot act as a closing ':' or
   terminator). Provenance + executable soundness check: mapping.md /
   axiom_check.py (G-AX validates this model against the real classifier). -/
def metaScan : List Char → Char → Bool
  | [], _ => false
  | c :: cs, prev =>
    if c = ':' then
      match cs with
      | [] => decide (prev ≠ ' ')
      | d :: _ =>
        if d = ' ' then decide (prev ≠ ' ')
        else if d = '`' then false
        else metaScan cs c
    else if c = '\\' then
      match cs with
      | [] => false
      | _ :: ds => metaScan ds (cs.headD ' ')
    else
      metaScan cs c

/- A line is a metadata line when it starts with ':' followed by a non-space,
   non-colon character, and the forward scan from that point finds a terminating
   ':'. The leading ':' serves as the scan's initial predecessor character. -/
def isMetadataLine : List Char → Bool
  | [] => false
  | [_] => false
  | a :: b :: rest =>
    if a = ':' && b ≠ ':' && b ≠ ' ' then metaScan (b :: rest) ':' else false

/- The number of leading lines (a prefix run) that are metadata lines: count
   from the front, stopping at the first line that is not a metadata line.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def leadingMetadata : List (List Char) → Nat
  | []          => 0
  | line :: rest => if isMetadataLine line then 1 + leadingMetadata rest else 0

@[grind] lemma leadingMetadata_nil : leadingMetadata [] = 0 := rfl
@[grind] lemma leadingMetadata_cons (line : List Char) (rest : List (List Char)) :
    leadingMetadata (line :: rest)
      = (if isMetadataLine line then 1 + leadingMetadata rest else 0) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The drop-step: dropping `i` instead of `i+1` exposes the line at index `i`
   on the front. The single goal `loom_solve` leaves for the loop body. -/
lemma drop_step (content : List (List Char)) (i : Nat) (hlt : i < content.length) :
    content.drop i = content[i]! :: content.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  rw [h]

/- One forward step: when the line at `i` is a metadata line, `leadingMetadata`
   of the suffix peels one off. -/
lemma leadingMetadata_step (content : List (List Char)) (i : Nat)
    (h : i < content.length) (hp : isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 1 + leadingMetadata (content.drop (i + 1)) := by
  rw [drop_step content i h, leadingMetadata_cons, if_pos hp]

/- Termination: when the loop stops (suffix exhausted, or the current line is
   not a metadata line), the remaining prefix run is empty. -/
lemma leadingMetadata_stop (content : List (List Char)) (i : Nat)
    (h : i ≤ content.length)
    (hd : i = content.length ∨ ¬ isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 0 := by
  by_cases hi : i = content.length
  · subst hi; rw [List.drop_length, leadingMetadata_nil]
  · have hlt : i < content.length := lt_of_le_of_ne h hi
    rw [drop_step content i hlt, leadingMetadata_cons, if_neg]
    rcases hd with h1 | h2
    · exact absurd h1 hi
    · simpa using h2

method countLeadingMetadataLines (content : List (List Char)) return (pos : Nat)
  ensures pos = leadingMetadata content
  do
    -- impl-start
    let mut i := 0
    while i < content.length ∧ isMetadataLine content[i]!
      invariant i ≤ content.length
      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
    do
      i := i + 1
    return i
    -- impl-end

prove_correct countLeadingMetadataLines by
  loom_solve
  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
      at invariant_2
    omega
  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
    omega
```

Prepatch bug re-encoded as an attack: `True`.

 All attacks same_spec==True (verified via swebench_unified.markers.same_spec, velvet backend).

### ATTACK RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch)
- atk_1.lean  `let _ := content; return 0`  (constant / partial-domain)          -> EXIT 1 (rejected: `0 = leadingMetadata content` unsolved). GOOD.
- atk_2.lean  `return content.length`  (over-count all)                          -> EXIT 1 (rejected). GOOD.
- atk_3.lean  correct loop then `return i+1`  (off-by-one boundary)              -> EXIT 1 (rejected: omega refutes a+1=a). GOOD.
- atk_4.lean  PREPATCH loose classifier `looseMetadataLine` in guard (real bug) -> EXIT 1 (rejected: `isMetadataLine content[i]!=true` unavailable). GOOD. Reproduces the gold bug.
- atk_5.lean  `(content.filter isMetadataLine).length`  (count ALL, not leading) -> EXIT 1 (rejected). GOOD.
- atk_6.lean  guard `i+1 < content.length` (stop one early / undercount)         -> EXIT 1 (rejected). GOOD.
- atk_7.lean  `while True` with weak `invariant True` + real done_with, `return i`-> EXIT 1 (rejected: done_1 doesn't pin i). GOOD.
- atk_8.lean  `return leadingMetadata content`  (ungrounded-oracle ECHO)         -> EXIT 0 (VERIFIES). Behaviorally CORRECT. RESOLVE (see patches): faithful patch = gold, `run_resolve` => RESOLVED=True COMPLETED=True FLAKY=False (cmd: python run_resolve_atk8.py; container sweb.eval.sphinx-doc__sphinx-11445...p566848). CORRECT ECHO, not a weakness.

### EXTRA CONTROL-FLOW ATTACKS (partial-correctness vacuity probe)
- atk_9.lean  `while True invariant True done_with (i = leadingMetadata content) do i:=i; return i` -> EXIT 0 (VERIFIES). This is vacuous partial correctness. FAITHFUL PATCH = infinite loop in prepend_prolog; `run_resolve(...,timeout=150,retries=0)` => COMPLETED=False (no report; harness hung) => INCONCLUSIVE class, NOT a break (build_one.py `_derive_audit_verdict`: `if r.completed and not r.resolved: BROKEN` else `if not r.completed: inconclusive`). NOT submitted as a break.
- atk_10.lean `while True ... return 0`                                          -> EXIT 1 (rejected: post-loop 0=leadingMetadata & invariant step both fail). GOOD.
- probe_falsedone.lean  `while True ... done_with (i=leadingMetadata content ∧ (0:Nat)=1)` -> EXIT 0 (VERIFIES). PROVES atk_9 is pure partial-correctness vacuity, POSTCONDITION-INDEPENDENT: loop exit is unreachable (¬True=False), so done_with is assumed from False. This is a universal property of `set_option loom.semantics.termination "partial"` (documented in prompts/velvet/spec_guide.md §1.1), NOT a defect of this spec; it would 'break' every partial-correctness bundle identically and cannot be the G-EQ standard.

### Positive control
- positive_control.lean = shipped Solution.lean (while + strong invariant + done + drop_step/leadingMetadata_step/leadingMetadata_stop proofs) -> EXIT 0 (VERIFIES). Spec non-vacuous.
- prepatch.lean = shipped Solution_prepatch.lean: same_spec==True, verify EXIT 1 (G-DIFF holds; loose `:\w+:` classifier over-counts `:role:`backtick markers so `pos = leadingMetadata content` unprovable).

### A-LEG / DEEP-MODEL AUDIT (the focus per prompt)
Axioms region EMPTY -> zero A-consumed legs. The ONLY kind-A obligation is the A-reference deep model `isMetadataLine`/`metaScan` == real `re.compile(Body.patterns['field_marker']).match` (post-patch classifier).
- Shipped axiom_check.py: EXIT 0 (37 boundary + 200k fuzz, 0 mismatches). docutils 0.23 present; field_marker pattern == mapping.md value verbatim: ':(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)'.
- INDEPENDENT fuzz (indep_ax.py, seed 999331, rich alphabet incl regex-metachars *+?[](){}|^$.- and unicode é 中, tab/VT/FF): 0 mismatches over 500,000 NEWLINE-FREE inputs; 0 mismatches on ALL reachable test lines (:title:/:author:/:mod:`foo`/----------/hello/-*10/...). Divergence appears ONLY with embedded \n/\r (4/200k with newlines allowed) — UNREACHABLE: a StringList element is a single source line and never contains a line terminator (confirmed vs the real prepend_prolog at rst.py). Matches prior verdict's finding. A-reference correspondence HOLDS on the reachable domain.

### REFINEMENT.MD LEG AUDIT (no kind-3)
Every leg is R / A-reference / I: A1 param (R, StringList↔List (List Char)); A2 init (I); A3 loop guard = I transliteration of `for..else:break` + A-reference deep model of `FIELD_NAME_RE.match`; A4 increment (I); A5 return (R). §B insertion arithmetic is an unchanged I leg driven by pos. §C: the one CHANGED op (classifier docinfo_re->FIELD_NAME_RE) is modeled DEEPLY (A-reference), not hidden behind a consumed axiom; NO kind-3. Verified against real repo: prepend_prolog leading loop matches, gold swaps docinfo_re->FIELD_NAME_RE exactly (patch.diff = gold verbatim).

### Conclusion
No verifying, behaviorally-wrong impl whose faithful patch completes-and-fails-to-resolve exists. 8 same-spec attacks run (6 rejected, 1 correct-echo whose patch RESOLVES, 1 partial-correctness-vacuity that is postcondition-independent and whose patch does not COMPLETE). Positive control verifies; prepatch reproduces the bug. Deep-model A-reference sound on reachable domain. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, verifying, behaviorally-WRONG impl exists whose faithful refined patch fails to resolve. The postcondition `pos = leadingMetadata content` is a TOTAL functional equality to a fully-concrete pure fold, so any terminating verifying impl computes exactly the correct count. The only verifying attack (atk_8, `return leadingMetadata content`) is behaviorally CORRECT; its faithful refined patch = the gold patch, which RESOLVED=True COMPLETED=True. The only OTHER verifying construct is atk_9 (`while True` partial-correctness vacuity), which is postcondition-INDEPENDENT (probe_falsedone verifies with a literally-false `done_with (... ∧ 0=1)`) and whose faithful infinite-loop patch does NOT complete (COMPLETED=False → inconclusive class per build_one.py:306-312, NOT a `completed ∧ ¬resolved` break). It is the sanctioned `termination "partial"` escape hatch (spec_guide §1.1), uniform across all partial-correctness bundles, not a weakness of this spec.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Whether a single text line is recognised by the strict line-classifier this
   module relies on (a standard reStructuredText line-classification grammar).

   A line is classified when it begins with ':' immediately followed by a
   character that is neither ':' nor a space, and then — scanning forward over
   the remaining characters — a ':' is reached that is *terminated* (it is the
   last character, or the next character is a space) while the character just
   before that closing ':' is not a space. A ':' that is immediately followed by
   a backtick does NOT terminate the marker (so an inline cross-reference such
   as `:role:` followed by a backtick is rejected). A backslash escapes the
   following character (the escaped character cannot act as a closing ':' or
   terminator). Provenance + executable soundness check: mapping.md /
   axiom_check.py (G-AX validates this model against the real classifier). -/
def metaScan : List Char → Char → Bool
  | [], _ => false
  | c :: cs, prev =>
    if c = ':' then
      match cs with
      | [] => decide (prev ≠ ' ')
      | d :: _ =>
        if d = ' ' then decide (prev ≠ ' ')
        else if d = '`' then false
        else metaScan cs c
    else if c = '\\' then
      match cs with
      | [] => false
      | _ :: ds => metaScan ds (cs.headD ' ')
    else
      metaScan cs c

/- A line is a metadata line when it starts with ':' followed by a non-space,
   non-colon character, and the forward scan from that point finds a terminating
   ':'. The leading ':' serves as the scan's initial predecessor character. -/
def isMetadataLine : List Char → Bool
  | [] => false
  | [_] => false
  | a :: b :: rest =>
    if a = ':' && b ≠ ':' && b ≠ ' ' then metaScan (b :: rest) ':' else false

/- The number of leading lines (a prefix run) that are metadata lines: count
   from the front, stopping at the first line that is not a metadata line.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def leadingMetadata : List (List Char) → Nat
  | []          => 0
  | line :: rest => if isMetadataLine line then 1 + leadingMetadata rest else 0

@[grind] lemma leadingMetadata_nil : leadingMetadata [] = 0 := rfl
@[grind] lemma leadingMetadata_cons (line : List Char) (rest : List (List Char)) :
    leadingMetadata (line :: rest)
      = (if isMetadataLine line then 1 + leadingMetadata rest else 0) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The drop-step: dropping `i` instead of `i+1` exposes the line at index `i`
   on the front. The single goal `loom_solve` leaves for the loop body. -/
lemma drop_step (content : List (List Char)) (i : Nat) (hlt : i < content.length) :
    content.drop i = content[i]! :: content.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  rw [h]

/- One forward step: when the line at `i` is a metadata line, `leadingMetadata`
   of the suffix peels one off. -/
lemma leadingMetadata_step (content : List (List Char)) (i : Nat)
    (h : i < content.length) (hp : isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 1 + leadingMetadata (content.drop (i + 1)) := by
  rw [drop_step content i h, leadingMetadata_cons, if_pos hp]

/- Termination: when the loop stops (suffix exhausted, or the current line is
   not a metadata line), the remaining prefix run is empty. -/
lemma leadingMetadata_stop (content : List (List Char)) (i : Nat)
    (h : i ≤ content.length)
    (hd : i = content.length ∨ ¬ isMetadataLine content[i]!) :
    leadingMetadata (content.drop i) = 0 := by
  by_cases hi : i = content.length
  · subst hi; rw [List.drop_length, leadingMetadata_nil]
  · have hlt : i < content.length := lt_of_le_of_ne h hi
    rw [drop_step content i hlt, leadingMetadata_cons, if_neg]
    rcases hd with h1 | h2
    · exact absurd h1 hi
    · simpa using h2

method countLeadingMetadataLines (content : List (List Char)) return (pos : Nat)
  ensures pos = leadingMetadata content
  do
    -- impl-start
    let mut i := 0
    while i < content.length ∧ isMetadataLine content[i]!
      invariant i ≤ content.length
      invariant leadingMetadata content = i + leadingMetadata (content.drop i)
      done_with (i = content.length ∨ ¬ isMetadataLine content[i]!)
    do
      i := i + 1
    return i
    -- impl-end

prove_correct countLeadingMetadataLines by
  loom_solve
  · rw [leadingMetadata_step content i ‹i < content.length› ‹isMetadataLine content[i]! = true›]
      at invariant_2
    omega
  · rw [leadingMetadata_stop content i invariant_1 done_1] at invariant_2
    omega
```

Prepatch bug re-encoded as an attack: `True`.

 All attacks same_spec==True (verified via swebench_unified.markers.same_spec, velvet backend).

### ATTACK RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch)
- atk_1.lean  `let _ := content; return 0`  (constant / partial-domain)          -> EXIT 1 (rejected: `0 = leadingMetadata content` unsolved). GOOD.
- atk_2.lean  `return content.length`  (over-count all)                          -> EXIT 1 (rejected). GOOD.
- atk_3.lean  correct loop then `return i+1`  (off-by-one boundary)              -> EXIT 1 (rejected: omega refutes a+1=a). GOOD.
- atk_4.lean  PREPATCH loose classifier `looseMetadataLine` in guard (real bug) -> EXIT 1 (rejected: `isMetadataLine content[i]!=true` unavailable). GOOD. Reproduces the gold bug.
- atk_5.lean  `(content.filter isMetadataLine).length`  (count ALL, not leading) -> EXIT 1 (rejected). GOOD.
- atk_6.lean  guard `i+1 < content.length` (stop one early / undercount)         -> EXIT 1 (rejected). GOOD.
- atk_7.lean  `while True` with weak `invariant True` + real done_with, `return i`-> EXIT 1 (rejected: done_1 doesn't pin i). GOOD.
- atk_8.lean  `return leadingMetadata content`  (ungrounded-oracle ECHO)         -> EXIT 0 (VERIFIES). Behaviorally CORRECT. RESOLVE (see patches): faithful patch = gold, `run_resolve` => RESOLVED=True COMPLETED=True FLAKY=False (cmd: python run_resolve_atk8.py; container sweb.eval.sphinx-doc__sphinx-11445...p566848). CORRECT ECHO, not a weakness.

### EXTRA CONTROL-FLOW ATTACKS (partial-correctness vacuity probe)
- atk_9.lean  `while True invariant True done_with (i = leadingMetadata content) do i:=i; return i` -> EXIT 0 (VERIFIES). This is vacuous partial correctness. FAITHFUL PATCH = infinite loop in prepend_prolog; `run_resolve(...,timeout=150,retries=0)` => COMPLETED=False (no report; harness hung) => INCONCLUSIVE class, NOT a break (build_one.py `_derive_audit_verdict`: `if r.completed and not r.resolved: BROKEN` else `if not r.completed: inconclusive`). NOT submitted as a break.
- atk_10.lean `while True ... return 0`                                          -> EXIT 1 (rejected: post-loop 0=leadingMetadata & invariant step both fail). GOOD.
- probe_falsedone.lean  `while True ... done_with (i=leadingMetadata content ∧ (0:Nat)=1)` -> EXIT 0 (VERIFIES). PROVES atk_9 is pure partial-correctness vacuity, POSTCONDITION-INDEPENDENT: loop exit is unreachable (¬True=False), so done_with is assumed from False. This is a universal property of `set_option loom.semantics.termination "partial"` (documented in prompts/velvet/spec_guide.md §1.1), NOT a defect of this spec; it would 'break' every partial-correctness bundle identically and cannot be the G-EQ standard.

### Positive control
- positive_control.lean = shipped Solution.lean (while + strong invariant + done + drop_step/leadingMetadata_step/leadingMetadata_stop proofs) -> EXIT 0 (VERIFIES). Spec non-vacuous.
- prepatch.lean = shipped Solution_prepatch.lean: same_spec==True, verify EXIT 1 (G-DIFF holds; loose `:\w+:` classifier over-counts `:role:`backtick markers so `pos = leadingMetadata content` unprovable).

### A-LEG / DEEP-MODEL AUDIT (the focus per prompt)
Axioms region EMPTY -> zero A-consumed legs. The ONLY kind-A obligation is the A-reference deep model `isMetadataLine`/`metaScan` == real `re.compile(Body.patterns['field_marker']).match` (post-patch classifier).
- Shipped axiom_check.py: EXIT 0 (37 boundary + 200k fuzz, 0 mismatches). docutils 0.23 present; field_marker pattern == mapping.md value verbatim: ':(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)'.
- INDEPENDENT fuzz (indep_ax.py, seed 999331, rich alphabet incl regex-metachars *+?[](){}|^$.- and unicode é 中, tab/VT/FF): 0 mismatches over 500,000 NEWLINE-FREE inputs; 0 mismatches on ALL reachable test lines (:title:/:author:/:mod:`foo`/----------/hello/-*10/...). Divergence appears ONLY with embedded \n/\r (4/200k with newlines allowed) — UNREACHABLE: a StringList element is a single source line and never contains a line terminator (confirmed vs the real prepend_prolog at rst.py). Matches prior verdict's finding. A-reference correspondence HOLDS on the reachable domain.

### REFINEMENT.MD LEG AUDIT (no kind-3)
Every leg is R / A-reference / I: A1 param (R, StringList↔List (List Char)); A2 init (I); A3 loop guard = I transliteration of `for..else:break` + A-reference deep model of `FIELD_NAME_RE.match`; A4 increment (I); A5 return (R). §B insertion arithmetic is an unchanged I leg driven by pos. §C: the one CHANGED op (classifier docinfo_re->FIELD_NAME_RE) is modeled DEEPLY (A-reference), not hidden behind a consumed axiom; NO kind-3. Verified against real repo: prepend_prolog leading loop matches, gold swaps docinfo_re->FIELD_NAME_RE exactly (patch.diff = gold verbatim).

### Conclusion
No verifying, behaviorally-wrong impl whose faithful patch completes-and-fails-to-resolve exists. 8 same-spec attacks run (6 rejected, 1 correct-echo whose patch RESOLVES, 1 partial-correctness-vacuity that is postcondition-independent and whose patch does not COMPLETE). Positive control verifies; prepatch reproduces the bug. Deep-model A-reference sound on reachable domain. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for velvet bundle sphinx-doc__sphinx-11445.

Modeled function: countLeadingMetadataLines(content: List (List Char)) ensures pos = leadingMetadata content, where leadingMetadata is the front-recursive count of the leading run of lines satisfying isMetadataLine, and isMetadataLine/metaScan deeply model the post-patch classifier FIELD_NAME_RE = re.compile(Body.patterns['field_marker']).match. Real callee: the leading-line counting loop in sphinx/util/rst.py:prepend_prolog (post-patch), which counts leading FIELD_NAME_RE.match(line) lines and breaks at the first non-match.

Verification: Solution.lean elaborates cleanly under lean_verify.sh (exit 0, 600s cap).

Core risk audited = deep-model fidelity of isMetadataLine vs the real docutils field_marker regex. I did NOT trust the bundle's port: I re-transliterated metaScan/isMetadataLine independently from the Lean source (respecting the exact match order and the prev-threading, backslash-escape, and backtick-guard cases) and differentially fuzzed against the REAL re.compile(Body.patterns['field_marker']).match (docutils 0.23; the pattern string is byte-identical to the one mapping.md/axiom_check.py assert: ':(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)').

Results:
- Broad alphabet including embedded '\n': 18 disagreements over 500k. Example ':X.1:\n' -> real=True, model=False; ':\\\n...:' -> real=False, model=True.
- ROOT CAUSE of every one of those 18: an embedded newline inside the line. With re.match and no re.MULTILINE, the '$' in '( +|$)' matches just before a trailing '\n', so the real regex accepts strings the model rejects (and backslash-before-newline cases flip the other way). These are NOT reachable inputs: StringList source lines are the RESULT of splitting a document on newlines, so a single line never contains an embedded '\n' (mapping.md sec 2 documents line <-> str per-code-point over the newline-free domain). Out of modeled domain -> not a defect.
- In-domain fuzz (newline removed from alphabet; alphabet = ': ` \\ a b c X Y Z . _ 0 1 2 3 < > ( ) [ ] { } tab é'), 1,000,000 random lines of length 0-16 plus a hand-built boundary battery (internal colons, trailing-space variants, backslash escapes, backtick-terminated role markers like ':mod:`foo`', empty/short lines): 0 disagreements.

Counting-loop / refinement level: real loop is `pos=0; for line in content: if RE.match(line): pos+=1 else: break` — a break-at-first-nonmatch prefix count, exactly leadingMetadata's front-recursive fold; the downstream insertion arithmetic depends only on pos and is behaviorally unchanged by the classifier swap. No over-strength: the postcondition pins exactly the observable quantity (the leading count) and nothing more.

Conclusion: the modeled function agrees with the real callee on every in-domain input tested (>1e6). No diverging in-domain input found; the spec does not drift from / over-constrain real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures) and swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean) == True — the spec region is byte-identical between patched and prepatch bundles, so the frozen consumer spec view is the audited one.

Spec view (computed via markers.spec_view) contents vs. gold edit: the gold patch swaps the loose classifier `docinfo_re = re.compile(':\\w+:.*?')` for the strict `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])` inside prepend_prolog (sphinx/util/rst.py), plus a defensive `lineno = 0`. Scanning the spec view for every repo-edit specific term — docinfo, field_marker, field_name, Body.patterns, prepend_prolog, rst.py, re.compile, docutils, sphinx, the `:\w+:` literal, diff markers — all return ABSENT. The only 'pattern' hit is the generic English word, no repo identifier.

What the spec view DOES expose is legitimate and PS-derivable: the discriminating behavior (a `:mod:`mypackage2`` role-with-backtick marker as the first heading is mis-handled when rst_prolog is set, over-counting the leading run) is fully present in the PUBLIC problem_statement. The spec re-expresses this at the grammar level via metaScan/isMetadataLine/leadingMetadata with a generic `:role:` placeholder and abstract prose ('a standard reStructuredText line-classification grammar', backtick-guard rejects inline cross-reference roles). This is the necessary definition-of-correct any spec must pin, expressed as the natural RST-literate generalization of the publicly-shown `:mod:` symptom — it reveals no repo internal beyond the problem_statement. Comment references (axiom_check.py, mapping.md, plan §5.4) point at bundle-internal audit artifacts, not the gold edit. No bug/fix narration in spec-view comments.

Not a RELAXED case: a faithful non-leaking PS-derivable spec is achievable and this is one; there is no PS↔gold mismatch forcing leakage. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
