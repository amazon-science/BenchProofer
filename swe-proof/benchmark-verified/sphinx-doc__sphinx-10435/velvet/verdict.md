# P2 adversarial audit — sphinx-doc__sphinx-10435

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk2_no_open_marker.lean`, `atk3_bare_trailer.lean`, `atk4_take14.lean`, `atk5_take16.lean`, `atk6_control_flow.lean`, `atk7_extra_char.lean`, `atk9_echo_unfold.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's postcondition is a full-output byte equality `out = wrapped (renderedInline snippet)`, where `wrapped body = codeOpen ++ ['%','\n'] ++ body ++ ['%','\n','}','}']`. Every same-spec impl whose behavior diverges from the gold on any input fails to verify: the residual `prove_correct` goal rejects the mismatched concrete term. No same-spec, VERIFYING, wrong-behavior implementation exists, so there is no verifying impl whose faithful refined patch fails to resolve.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,13 +128,17 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
+    -- Pre-image skeleton: the macro opening is substituted WITHOUT the
+    -- line-break-suppressing marker, only the closing control sequence (not the
+    -- newline preceding it) is dropped, and the trailer is the bare closing
+    -- braces. The line breaks around the body therefore survive and the frozen
+    -- spec `out = wrapped (renderedInline snippet)` is NOT met, so prove_correct
+    -- MUST fail.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
-    let hlcode := openTok ++ hlcode.drop beginTok.length
+    let hlcode := codeOpen ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    let hlcode := stripped.take (stripped.length - 14)
+    return hlcode ++ ['}', '}']
     -- impl-end
 end
 
```

Attack 2 — `atk2_no_open_marker.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,10 +128,8 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
-    let hlcode := openTok ++ hlcode.drop beginTok.length
+    let hlcode := codeOpen ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
     let hlcode := stripped.take (stripped.length - 15)
     return hlcode ++ ['%', '\n', '}', '}']
```

Attack 3 — `atk3_bare_trailer.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,13 +128,11 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
     let hlcode := openTok ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
     let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    return hlcode ++ ['}', '}']
     -- impl-end
 end
 
```

Attack 4 — `atk4_take14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,12 +128,10 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
     let hlcode := openTok ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
+    let hlcode := stripped.take (stripped.length - 14)
     return hlcode ++ ['%', '\n', '}', '}']
     -- impl-end
 end
```

Attack 5 — `atk5_take16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,12 +128,10 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
     let hlcode := openTok ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
+    let hlcode := stripped.take (stripped.length - 16)
     return hlcode ++ ['%', '\n', '}', '}']
     -- impl-end
 end
```

Attack 6 — `atk6_control_flow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,16 +128,16 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
-    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
-    let hlcode := openTok ++ hlcode.drop beginTok.length
-    let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    match snippet with
+    | [] => return []
+    | _ =>
+      let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
+      let hlcode := openTok ++ hlcode.drop beginTok.length
+      let stripped := rstrip hlcode
+      let hlcode := stripped.take (stripped.length - 15)
+      return hlcode ++ ['%', '\n', '}', '}']
     -- impl-end
 end
 
 prove_correct wrapInlineCode by
-  loom_solve
-  rw [choice_1, compute (renderedInline snippet)]
+  loom_solve <;> (try (rw [choice_1, compute (renderedInline snippet)]))
```

Attack 7 — `atk7_extra_char.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,13 +128,11 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
     let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
     let hlcode := openTok ++ hlcode.drop beginTok.length
     let stripped := rstrip hlcode
     let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    return hlcode ++ ['%', '\n', '}', '}', '!']
     -- impl-end
 end
 
```

Attack 8 — `atk8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -128,16 +128,9 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
-    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
-    let hlcode := openTok ++ hlcode.drop beginTok.length
-    let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    return wrapped (renderedInline snippet)
     -- impl-end
 end
 
 prove_correct wrapInlineCode by
   loom_solve
-  rw [choice_1, compute (renderedInline snippet)]
```

Attack 9 — `atk9_echo_unfold.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,16 +128,10 @@
   ensures out = wrapped (renderedInline snippet)
   do
     -- impl-start
-    -- Render the snippet (unchanged highlighter callee), then perform the
-    -- macro substitution and trailer surgery.
-    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
-    let hlcode := openTok ++ hlcode.drop beginTok.length
-    let stripped := rstrip hlcode
-    let hlcode := stripped.take (stripped.length - 15)
-    return hlcode ++ ['%', '\n', '}', '}']
+    let body := renderedInline snippet
+    return codeOpen ++ ['%', '\n'] ++ body ++ ['%', '\n', '}', '}']
     -- impl-end
 end
 
 prove_correct wrapInlineCode by
   loom_solve
-  rw [choice_1, compute (renderedInline snippet)]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total-correctness semantics: the routine under spec is straight-line (a
   render call followed by bounded list surgery; no loops or recursion — it
   always returns), so the contract also demands termination. Under partial
   semantics a diverging body would vacuously satisfy every postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The syntax-highlighter's rendering of one inline code snippet, as a pure
   function on code points. It is an UNCHANGED callee: the routine under spec
   calls it and does not alter it. The only structural fact the spec relies on
   is `highlightInline_form`: the rendered text is a constant opening control
   sequence, then a newline, then the rendered body, then a newline, then a
   constant closing control sequence, then a final newline. We pin nothing about
   the body content (`renderedInline`) — the weakest sufficient contract is the
   surrounding frame (directive 7). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom renderedInline : List Char → List Char
-- axioms-end

-- pure-start
/- The constant opening control sequence emitted by the highlighter's block
   formatter (length 37 code points). -/
def beginTok : List Char := "\\begin{Verbatim}[commandchars=\\\\\\{\\}]".toList

/- The constant closing control sequence emitted by the highlighter's block
   formatter (length 14 code points). -/
def endTok : List Char := "\\end{Verbatim}".toList

/- The inline-code macro opening (length 27 code points). -/
def codeOpen : List Char := "\\sphinxcode{\\sphinxupquote{".toList

/- The opening as the routine substitutes it: the inline-code macro opening
   immediately followed by a line-break-suppressing comment marker, so the
   line break that follows does not render as a leading space. -/
def openTok : List Char := codeOpen ++ ['%']

/- Drop trailing whitespace (the model of the standard right-strip). -/
def rstrip (s : List Char) : List Char := (s.reverse.dropWhile Char.isWhitespace).reverse

/- The desired wrapped markup for an inline snippet with rendered body `body`:
   the code-macro opening, a line-break-suppressing marker, a newline, the
   rendered body, a line-break-suppressing marker, a newline, and the closing
   braces. The two markers make the surrounding line breaks produce no spurious
   whitespace in the output. -/
def wrapped (body : List Char) : List Char :=
  codeOpen ++ ['%', '\n'] ++ body ++ ['%', '\n', '}', '}']

/- The non-deterministic choice of the highlighter's result is well-posed: for
   any target value `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choice
   elaborates. It does NOT weaken verification: under demonic choice the
   postcondition must still hold for every value the predicate allows, here
   exactly the framed rendering. -/
noncomputable instance findableEqList (v : List Char) (n : Lean.Name) :
    Findable (fun e : List Char => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

@[grind] lemma endTok_len : endTok.length = 14 := by unfold endTok; rfl

/- The arithmetic-and-slicing core: substituting the opening for the leading
   control sequence, right-stripping the single trailing newline, dropping the
   final closing control sequence together with the newline preceding it, then
   appending the line-break-suppressing marker and the closing braces, yields
   exactly `wrapped body`. Proven by structural rewriting of the concatenation;
   this is the single goal `loom_solve` leaves for the routine. -/
lemma compute (body : List Char) :
    List.take
      ((rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))).length - 15)
      (rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))) ++ ['%', '\n', '}', '}']
    = wrapped body := by
  have hdrop : List.drop beginTok.length
      (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'] := by
    have : beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']
        = beginTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']) := by
      simp [List.append_assoc]
    rw [this, List.drop_left]
  rw [hdrop]
  have hre : openTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'] := by
    simp [List.append_assoc]
  rw [hre]
  have hrs : rstrip ((openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok := by
    unfold rstrip endTok; simp [List.reverse_append]
  rw [hrs]
  have hre2 : (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok
      = (openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok) := by
    simp [List.append_assoc]
  rw [hre2]
  have hlen : ((openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok)).length - 15
      = (openTok ++ ['\n'] ++ body).length := by
    simp only [List.length_append, List.length_cons, List.length_nil, endTok_len]; omega
  rw [hlen, List.take_left]
  unfold wrapped openTok; simp [List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap one highlighted inline code snippet for the document writer.

   The desired behavior: the snippet is rendered by the syntax highlighter and
   then wrapped in the inline-code macro. The result is exactly `wrapped` of the
   rendered body — the macro opening and the rendered body are each immediately
   followed by a line-break-suppressing marker, so the line breaks that the
   highlighter places around the body do not render as a spurious space at the
   start and end of the inline code (`out = wrapped (renderedInline snippet)`).

   `snippet` is the read-only input source text (not `mut`): the routine renders
   it and never alters it (directive 5). Both the snippet and the rendered text
   are modeled as `List Char` (per-code-point strings; mapping.md §2). -/
noncomputable section
method wrapInlineCode (snippet : List Char) return (out : List Char)
  ensures out = wrapped (renderedInline snippet)
  do
    -- impl-start
    -- Render the snippet (unchanged highlighter callee), then perform the
    -- macro substitution and trailer surgery.
    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
    let hlcode := openTok ++ hlcode.drop beginTok.length
    let stripped := rstrip hlcode
    let hlcode := stripped.take (stripped.length - 15)
    return hlcode ++ ['%', '\n', '}', '}']
    -- impl-end
end

prove_correct wrapInlineCode by
  loom_solve
  rw [choice_1, compute (renderedInline snippet)]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed Same-spec confirmed True for all 9 attacks + positive_control via swebench_unified.markers.same_spec (velvet). same_spec elides both the impl region and the prove_correct body, so impl+proof were the only edits; axioms/pure/pre/post left byte-identical.

Commands: `bash scripts/lean_verify.sh <file>` run concurrently in batches of <=4.

### VERIFY RESULTS (exit codes):
- positive_control.lean = 0 (VERIFIES, correct impl) [positive control PASS]
- atk_prepatch.lean = 1 (prepatch bug reproduced: codeOpen w/o %, take -14, bare '}}' trailer; residual goal `... ++ ['}','}'] = wrapped body` is false)
- atk2_no_open_marker.lean = 1 (codeOpen instead of openTok: missing leading %)
- atk3_bare_trailer.lean = 1 (return `... ++ ['}','}']`: missing %\n before braces)
- atk4_take14.lean = 1 (boundary/off-by-one: take length-14 keeps pre-END newline)
- atk5_take16.lean = 1 (boundary/off-by-one: take length-16 drops extra char)
- atk6_control_flow.lean = 1 (control-flow-effect: empty-snippet branch returns []; residual goal `[] = wrapped (...)`)
- atk7_extra_char.lean = 1 (partial-domain/extra trailing '!' char)
- atk8_echo.lean = 0 (VERIFIES; ungrounded-oracle echo: `return wrapped (renderedInline snippet)` — byte-identical to gold output)
- atk9_echo_unfold.lean = 1 (correct OUTPUT written in unfolded form; fails only because loom_solve doesn't unfold `wrapped` — proof-strength artifact, NOT a spec weakness; behavior is gold-equivalent so no risk)

No wrong-BEHAVIOR impl verifies. The only two verifying impls (positive_control, atk8_echo) both emit exactly `wrapped (renderedInline snippet)` = the post-fix byte sequence.

RESOLVE (protocol step 2): materialized atk8_echo's faithful refined patch. Because its output is byte-identical to the gold's post-fix markup, the faithful patch IS the gold patch.diff verbatim. Ran the official harness: `run_resolve('sphinx-doc__sphinx-10435', patch)` => RESOLVED=True, COMPLETED=True, note='resolved'. So the verifying echo resolves — consistent with the RESOLVED 2026-08-06 echo-attack policy (a resolving echo of the gold is NOT a weakness). verify => resolve holds.

REFINEMENT.MD AUDIT: legs are R (A0/A2/A4/A5 refinement parts) / A-consumed (A1 only, the UNCHANGED highlight_block callee modeled by its structural frame BEGIN(37)+\n+body+\n+END(14)+\n, consumed by lemma `compute`) / I (concrete slice/concat ops). Zero kind-3 (inexpressible-changed-op) legs; the changed ops (+%, -14->-15, }}->%\n}}) are all concrete List Char ops (R+I). The single A-leg's correspondence to the real callee (PygmentsBridge('latex').highlight_block, highlighting.py:136) is validated by G-AX/axiom_check.py; A-reference appears only in the legend and in A1's explicit 'NOT an A-reference' note (frame-only, not a deep body model). Correspondence holds.

Verdict SOUND: >=5 distinct wrong impls run (8 wrong + prepatch), none verifies; the sole verifying non-trivial candidate (echo) resolves under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk2_no_open_marker.lean`, `atk3_bare_trailer.lean`, `atk4_take14.lean`, `atk5_take16.lean`, `atk6_control_flow.lean`, `atk7_extra_char.lean`, `atk9_echo_unfold.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's postcondition is a full-output byte equality `out = wrapped (renderedInline snippet)`, where `wrapped body = codeOpen ++ ['%','\n'] ++ body ++ ['%','\n','}','}']`. Every same-spec impl whose behavior diverges from the gold on any input fails to verify: the residual `prove_correct` goal rejects the mismatched concrete term. No same-spec, VERIFYING, wrong-behavior implementation exists, so there is no verifying impl whose faithful refined patch fails to resolve.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_no_open_marker.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_bare_trailer.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_take14.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_take16.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_control_flow.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_extra_char.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk9_echo_unfold.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total-correctness semantics: the routine under spec is straight-line (a
   render call followed by bounded list surgery; no loops or recursion — it
   always returns), so the contract also demands termination. Under partial
   semantics a diverging body would vacuously satisfy every postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The syntax-highlighter's rendering of one inline code snippet, as a pure
   function on code points. It is an UNCHANGED callee: the routine under spec
   calls it and does not alter it. The only structural fact the spec relies on
   is `highlightInline_form`: the rendered text is a constant opening control
   sequence, then a newline, then the rendered body, then a newline, then a
   constant closing control sequence, then a final newline. We pin nothing about
   the body content (`renderedInline`) — the weakest sufficient contract is the
   surrounding frame (directive 7). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom renderedInline : List Char → List Char
-- axioms-end

-- pure-start
/- The constant opening control sequence emitted by the highlighter's block
   formatter (length 37 code points). -/
def beginTok : List Char := "\\begin{Verbatim}[commandchars=\\\\\\{\\}]".toList

/- The constant closing control sequence emitted by the highlighter's block
   formatter (length 14 code points). -/
def endTok : List Char := "\\end{Verbatim}".toList

/- The inline-code macro opening (length 27 code points). -/
def codeOpen : List Char := "\\sphinxcode{\\sphinxupquote{".toList

/- The opening as the routine substitutes it: the inline-code macro opening
   immediately followed by a line-break-suppressing comment marker, so the
   line break that follows does not render as a leading space. -/
def openTok : List Char := codeOpen ++ ['%']

/- Drop trailing whitespace (the model of the standard right-strip). -/
def rstrip (s : List Char) : List Char := (s.reverse.dropWhile Char.isWhitespace).reverse

/- The desired wrapped markup for an inline snippet with rendered body `body`:
   the code-macro opening, a line-break-suppressing marker, a newline, the
   rendered body, a line-break-suppressing marker, a newline, and the closing
   braces. The two markers make the surrounding line breaks produce no spurious
   whitespace in the output. -/
def wrapped (body : List Char) : List Char :=
  codeOpen ++ ['%', '\n'] ++ body ++ ['%', '\n', '}', '}']

/- The non-deterministic choice of the highlighter's result is well-posed: for
   any target value `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choice
   elaborates. It does NOT weaken verification: under demonic choice the
   postcondition must still hold for every value the predicate allows, here
   exactly the framed rendering. -/
noncomputable instance findableEqList (v : List Char) (n : Lean.Name) :
    Findable (fun e : List Char => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

@[grind] lemma endTok_len : endTok.length = 14 := by unfold endTok; rfl

/- The arithmetic-and-slicing core: substituting the opening for the leading
   control sequence, right-stripping the single trailing newline, dropping the
   final closing control sequence together with the newline preceding it, then
   appending the line-break-suppressing marker and the closing braces, yields
   exactly `wrapped body`. Proven by structural rewriting of the concatenation;
   this is the single goal `loom_solve` leaves for the routine. -/
lemma compute (body : List Char) :
    List.take
      ((rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))).length - 15)
      (rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))) ++ ['%', '\n', '}', '}']
    = wrapped body := by
  have hdrop : List.drop beginTok.length
      (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'] := by
    have : beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']
        = beginTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']) := by
      simp [List.append_assoc]
    rw [this, List.drop_left]
  rw [hdrop]
  have hre : openTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'] := by
    simp [List.append_assoc]
  rw [hre]
  have hrs : rstrip ((openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok := by
    unfold rstrip endTok; simp [List.reverse_append]
  rw [hrs]
  have hre2 : (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok
      = (openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok) := by
    simp [List.append_assoc]
  rw [hre2]
  have hlen : ((openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok)).length - 15
      = (openTok ++ ['\n'] ++ body).length := by
    simp only [List.length_append, List.length_cons, List.length_nil, endTok_len]; omega
  rw [hlen, List.take_left]
  unfold wrapped openTok; simp [List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap one highlighted inline code snippet for the document writer.

   The desired behavior: the snippet is rendered by the syntax highlighter and
   then wrapped in the inline-code macro. The result is exactly `wrapped` of the
   rendered body — the macro opening and the rendered body are each immediately
   followed by a line-break-suppressing marker, so the line breaks that the
   highlighter places around the body do not render as a spurious space at the
   start and end of the inline code (`out = wrapped (renderedInline snippet)`).

   `snippet` is the read-only input source text (not `mut`): the routine renders
   it and never alters it (directive 5). Both the snippet and the rendered text
   are modeled as `List Char` (per-code-point strings; mapping.md §2). -/
noncomputable section
method wrapInlineCode (snippet : List Char) return (out : List Char)
  ensures out = wrapped (renderedInline snippet)
  do
    -- impl-start
    -- Render the snippet (unchanged highlighter callee), then perform the
    -- macro substitution and trailer surgery.
    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
    let hlcode := openTok ++ hlcode.drop beginTok.length
    let stripped := rstrip hlcode
    let hlcode := stripped.take (stripped.length - 15)
    return hlcode ++ ['%', '\n', '}', '}']
    -- impl-end
end

prove_correct wrapInlineCode by
  loom_solve
  rw [choice_1, compute (renderedInline snippet)]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed Same-spec confirmed True for all 9 attacks + positive_control via swebench_unified.markers.same_spec (velvet). same_spec elides both the impl region and the prove_correct body, so impl+proof were the only edits; axioms/pure/pre/post left byte-identical.

Commands: `bash scripts/lean_verify.sh <file>` run concurrently in batches of <=4.

### VERIFY RESULTS (exit codes):
- positive_control.lean = 0 (VERIFIES, correct impl) [positive control PASS]
- atk_prepatch.lean = 1 (prepatch bug reproduced: codeOpen w/o %, take -14, bare '}}' trailer; residual goal `... ++ ['}','}'] = wrapped body` is false)
- atk2_no_open_marker.lean = 1 (codeOpen instead of openTok: missing leading %)
- atk3_bare_trailer.lean = 1 (return `... ++ ['}','}']`: missing %\n before braces)
- atk4_take14.lean = 1 (boundary/off-by-one: take length-14 keeps pre-END newline)
- atk5_take16.lean = 1 (boundary/off-by-one: take length-16 drops extra char)
- atk6_control_flow.lean = 1 (control-flow-effect: empty-snippet branch returns []; residual goal `[] = wrapped (...)`)
- atk7_extra_char.lean = 1 (partial-domain/extra trailing '!' char)
- atk8_echo.lean = 0 (VERIFIES; ungrounded-oracle echo: `return wrapped (renderedInline snippet)` — byte-identical to gold output)
- atk9_echo_unfold.lean = 1 (correct OUTPUT written in unfolded form; fails only because loom_solve doesn't unfold `wrapped` — proof-strength artifact, NOT a spec weakness; behavior is gold-equivalent so no risk)

No wrong-BEHAVIOR impl verifies. The only two verifying impls (positive_control, atk8_echo) both emit exactly `wrapped (renderedInline snippet)` = the post-fix byte sequence.

RESOLVE (protocol step 2): materialized atk8_echo's faithful refined patch. Because its output is byte-identical to the gold's post-fix markup, the faithful patch IS the gold patch.diff verbatim. Ran the official harness: `run_resolve('sphinx-doc__sphinx-10435', patch)` => RESOLVED=True, COMPLETED=True, note='resolved'. So the verifying echo resolves — consistent with the RESOLVED 2026-08-06 echo-attack policy (a resolving echo of the gold is NOT a weakness). verify => resolve holds.

REFINEMENT.MD AUDIT: legs are R (A0/A2/A4/A5 refinement parts) / A-consumed (A1 only, the UNCHANGED highlight_block callee modeled by its structural frame BEGIN(37)+\n+body+\n+END(14)+\n, consumed by lemma `compute`) / I (concrete slice/concat ops). Zero kind-3 (inexpressible-changed-op) legs; the changed ops (+%, -14->-15, }}->%\n}}) are all concrete List Char ops (R+I). The single A-leg's correspondence to the real callee (PygmentsBridge('latex').highlight_block, highlighting.py:136) is validated by G-AX/axiom_check.py; A-reference appears only in the legend and in A1's explicit 'NOT an A-reference' note (frame-only, not a deep body model). Correspondence holds.

Verdict SOUND: >=5 distinct wrong impls run (8 wrong + prepatch), none verifies; the sole verifying non-trivial candidate (echo) resolves under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-10435 velvet bundle. Setup checks: (1) same_spec(Solution, Solution_prepatch) with velvet LanguageTables = True (spec region byte-identical). (2) Solution.lean elaborates cleanly via lean_verify.sh (exit 0, no sorry/error). base_commit f1061c012 confirmed pre-patch (latex.py:1710-1716 still has `\sphinxupquote{`, `[:-14]`, bare `}}`); patch.diff itself absent from bundle but the gold hunk is documented in refinement.md and matches the real post-patch behavior.

Modeled function: wrapInlineCode with `ensures out = wrapped (renderedInline snippet)`, wrapped body = codeOpen ++ ['%','\n'] ++ body ++ ['%','\n','}','}']. This models the post-patch inline-code branch of LaTeXTranslator.visit_literal: highlight_block -> .replace(BEGIN, codeOpen+'%') -> .rstrip()[:-15] -> append(hlcode)+append('%'+CR+'}}').

Built an oracle in a venv with the worktree sphinx (5.0.0, pygments 2.20.0) that runs the EXACT real post-patch branch (real highlight_block callee + .replace/.rstrip/[:-15]/append) and compares against the modeled `wrapped(body)` where body is reconstructed from the real callee's frame. Results:
 - 30243 in-frame observations across 9 languages (boundary + 30k seeded fuzz, seed 10435): ALL match, 0 mismatches. 'Could not lex' cases were NOT skipped — highlight_block warns and returns a frame-matching Verbatim fallback, so they too were checked and matched.
 - Structural-frame axiom (BEGIN len 37 prefix + '\n' + body + '\n' + END len 14 + '\n') held on every observation including adversarial bodies containing literal BEGIN/END tokens; 20k targeted frame-stress fuzz over \begin/\end/commandchars alphabet: 0 frame failures.
 - Potential .replace-vs-prefix-drop gap (global replace differs from prefix-drop only if BEGIN recurs in body): pygments always escapes/renders such content, so BEGIN never appears verbatim in body -> found_multi = 0. No divergence.
 - rstrip edge cases (bodies ending in spaces/tabs/newlines): real branch and model agree on all tested.

The spec has no precondition and claims equality for all snippets; the real callee's frame is total on the modeled branch (unlexable input falls back within-frame, not outside it), so the spec is not too strong. No diverging input found; the modeled function agrees with the real post-patch repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True — spec region (imports/axioms/pure/pre/post + method signature + ensures) is byte-identical between patched and prepatch; only impl and prove_correct bodies differ (both elided in the consumer spec view). Rendered the actual consumer spec view via markers.spec_view: impl region collapses to 'implementation elided' and the prove_correct body to 'proof elided'. 

Leakage assessment vs PUBLIC problem_statement (not hints): The GitHub issue itself proposes the exact fix. It shows the buggy markup ('\sphinxcode{\sphinxupquote{' followed by a spurious space, and '}}' preceded by a space) and explicitly states 'a priori, mark-up should be: \sphinxcode{\sphinxupquote{%' ... 'pass%' ... '}}'. So the whole behavioral content of the gold edit — the two line-break-suppressing '%' markers and the collapse of the surrounding newlines — is PUBLIC.

The spec view's disclosing symbols (openTok = codeOpen ++ ['%']; wrapped body = codeOpen ++ ['%','\n'] ++ body ++ ['%','\n','}','}']) are a direct formalization of the issue's published 'should be' block, not information beyond it. The only spec-view detail not literally in the issue is the '.length - 15' / trailer surgery in the `compute` lemma (pure region); but 15 = len(END)=14 + 1 pre-END newline is a derived consequence of the public desired output plus the G-AX-validated highlighter frame, not independent knowledge of the gold source diff. No file path, no line number, no Python code, no '[:-14]'/'[:-15]' verbatim, and no PYG tokens appear anywhere in the spec view.

The genuinely gold-specific artifacts — the verbatim gold hunk, 'latex.py:1712' line refs, and the Python 'rstrip()[:-14]'->'[:-15]' diff — live only in refinement.md and mapping.md (auditor docs), which are OUT OF SCOPE for the G-PANEL-3 spec-view leak screen. The consumer-facing spec view leaks nothing about the gold edit beyond what the public problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
