# P2 adversarial audit — sphinx-doc__sphinx-7590

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,7 @@
   let fl := floatMatch s
   if fl > 0 then
     return some (finishLiteral fl s floatSuffixMatch)
-  for m in [binMatch, hexMatch, decMatch, octMatch] do
+  for m in [octMatch, binMatch, hexMatch, decMatch] do
     let il := m s
     if il > 0 then
       return some (finishLiteral il s intSuffixMatch)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,7 @@
   let fl := floatMatch s
   if fl > 0 then
     return some (finishLiteral fl s floatSuffixMatch)
-  for m in [binMatch, hexMatch, decMatch, octMatch] do
+  for m in [binMatch, hexMatch, decMatch] do
     let il := m s
     if il > 0 then
       return some (finishLiteral il s intSuffixMatch)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,9 +113,6 @@
 
 -- impl-start
 def implementation_literalId (s : List Char) : Option String := Id.run do
-  let fl := floatMatch s
-  if fl > 0 then
-    return some (finishLiteral fl s floatSuffixMatch)
   for m in [binMatch, hexMatch, decMatch, octMatch] do
     let il := m s
     if il > 0 then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,7 +115,7 @@
 def implementation_literalId (s : List Char) : Option String := Id.run do
   let fl := floatMatch s
   if fl > 0 then
-    return some (finishLiteral fl s floatSuffixMatch)
+    return some (finishLiteral fl s intSuffixMatch)
   for m in [binMatch, hexMatch, decMatch, octMatch] do
     let il := m s
     if il > 0 then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,7 +115,7 @@
 def implementation_literalId (s : List Char) : Option String := Id.run do
   let fl := floatMatch s
   if fl > 0 then
-    return some (finishLiteral fl s floatSuffixMatch)
+    return some (finishLiteral (fl + 1) s floatSuffixMatch)
   for m in [binMatch, hexMatch, decMatch, octMatch] do
     let il := m s
     if il > 0 then
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -113,13 +113,13 @@
 
 -- impl-start
 def implementation_literalId (s : List Char) : Option String := Id.run do
-  let fl := floatMatch s
-  if fl > 0 then
-    return some (finishLiteral fl s floatSuffixMatch)
   for m in [binMatch, hexMatch, decMatch, octMatch] do
     let il := m s
     if il > 0 then
       return some (finishLiteral il s intSuffixMatch)
+  let fl := floatMatch s
+  if fl > 0 then
+    return some (finishLiteral fl s floatSuffixMatch)
   return none
 -- impl-end
 
```

Attack 7 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,11 +115,13 @@
 def implementation_literalId (s : List Char) : Option String := Id.run do
   let fl := floatMatch s
   if fl > 0 then
-    return some (finishLiteral fl s floatSuffixMatch)
+    let sfx := floatSuffixMatch (s.drop fl)
+    return some (numId (s.take (fl + sfx)))
   for m in [binMatch, hexMatch, decMatch, octMatch] do
     let il := m s
     if il > 0 then
-      return some (finishLiteral il s intSuffixMatch)
+      let sfx := intSuffixMatch (s.drop il)
+      return some (numId (s.take (il + sfx)))
   return none
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the mangled identifier of a parsed C++ numeric literal.

A C++ literal may be written bare (e.g. `5`, `6.62607015e-34`), with a standard
numeric type suffix (e.g. `5ul`, `5.0f`), or as a *user-defined literal*: the
bare literal immediately followed by an identifier, e.g. `6.62607015e-34q_J` or
`5_udl`. The desired behaviour is that all three forms are recognised and given
a mangled identifier:

* a bare numeric literal whose source text is `data` mangles to `"L" data "E"`;
* a literal carrying a standard numeric suffix keeps the suffix as part of its
  source text, so `data` includes the suffix and the mangling is again
  `"L" data "E"`;
* a user-defined literal — a bare literal (with NO standard suffix) directly
  followed by an identifier `ident` — mangles as if it were a call of the
  identifier on the literal: `"clL_Zli" (id ident) "E" (inner) "E"`, where
  `inner` is the mangling of the underlying bare literal and `(id ident)` is the
  identifier's own mangling: the reserved namespace name `std` mangles to its
  standard abbreviation `"St"`, any other identifier to its length in decimal
  followed by its text.

A standard suffix takes precedence over a user-defined identifier: a literal that
is immediately followed by a recognised suffix is a plain suffixed literal, never
a user-defined literal. The float forms are recognised before the integer forms,
and among integer forms the binary, hexadecimal, decimal and octal shapes are
tried in that order.
-/

-- axioms-start
-- The lexical recognisers below are primitive pattern matchers over the head of
-- the input: each returns the LENGTH of the prefix it consumes (0 = no match).
-- They are modeled as opaque callees so that they appear identically in the
-- specification and the implementation; the behaviour of interest is the CONTROL
-- FLOW that combines them (when a trailing identifier is folded into a
-- user-defined literal), not the internals of any single recogniser. No property
-- of any recogniser is consumed by the proof, so no `axiom … _prop` is declared.

/-- Length of a leading floating-point literal (0 if none). -/
opaque floatMatch : List Char → Nat
/-- Length of a leading standard float type suffix following a float literal. -/
opaque floatSuffixMatch : List Char → Nat
/-- Length of a leading binary integer literal. -/
opaque binMatch : List Char → Nat
/-- Length of a leading hexadecimal integer literal. -/
opaque hexMatch : List Char → Nat
/-- Length of a leading decimal integer literal. -/
opaque decMatch : List Char → Nat
/-- Length of a leading octal integer literal. -/
opaque octMatch : List Char → Nat
/-- Length of a leading standard integer type suffix following an integer literal. -/
opaque intSuffixMatch : List Char → Nat
/-- Length of a leading user-defined-literal identifier (0 if none). -/
opaque udlMatch : List Char → Nat
-- axioms-end

-- pure-start
/-- Mangling of a bare literal whose source text is `data`. -/
def numId (data : List Char) : String := "L" ++ String.mk data ++ "E"

/-- Mangling fragment of an identifier: the reserved namespace name `std`
mangles to its standard abbreviation `"St"`; any other identifier mangles as
its length in decimal followed by its text. -/
def identId (ident : List Char) : String :=
  if ident = "std".toList then "St"
  else toString ident.length ++ String.mk ident

/-- Mangling of a user-defined literal wrapping `inner` with identifier `ident`. -/
def udlId (ident : List Char) (inner : String) : String :=
  "clL_Zli" ++ identId ident ++ "E" ++ inner ++ "E"

/-- Given a base literal occupying the first `baseLen` chars of `s` and the
suffix recogniser `suffixMatch` for that literal class, produce the mangled id:
keep a standard suffix as part of the literal's text, otherwise try to fold a
trailing identifier into a user-defined literal, otherwise emit the bare id. -/
def finishLiteral (baseLen : Nat) (s : List Char)
    (suffixMatch : List Char → Nat) : String :=
  let rest := s.drop baseLen
  let sfx := suffixMatch rest
  if sfx > 0 then
    numId (s.take (baseLen + sfx))
  else
    let baseId := numId (s.take baseLen)
    let u := udlMatch rest
    if u > 0 then udlId (rest.take u) baseId else baseId

/-- First matching integer-literal length, trying binary, hex, decimal, octal. -/
def intMatchLen (s : List Char) : Option Nat :=
  let bs := binMatch s
  if bs > 0 then some bs else
  let hs := hexMatch s
  if hs > 0 then some hs else
  let ds := decMatch s
  if ds > 0 then some ds else
  let os := octMatch s
  if os > 0 then some os else none
-- pure-end

-- post-conditions-start
/-- The mangled id of the literal at the head of `s`: a float literal (with
optional suffix or trailing user-defined identifier) if one is present, else the
first matching integer literal (likewise), else none. -/
def problem_spec_literalId (s : List Char) (result : Option String) : Prop :=
  result =
    (let fl := floatMatch s
     if fl > 0 then some (finishLiteral fl s floatSuffixMatch)
     else match intMatchLen s with
          | some il => some (finishLiteral il s intSuffixMatch)
          | none => none)
-- post-conditions-end

-- impl-start
def implementation_literalId (s : List Char) : Option String := Id.run do
  let fl := floatMatch s
  if fl > 0 then
    return some (finishLiteral fl s floatSuffixMatch)
  for m in [binMatch, hexMatch, decMatch, octMatch] do
    let il := m s
    if il > 0 then
      return some (finishLiteral il s intSuffixMatch)
  return none
-- impl-end

-- proof-start
theorem correct_literalId :
    ∀ (s : List Char),
      problem_spec_literalId s (implementation_literalId s) := by
  intro s
  unfold problem_spec_literalId implementation_literalId intMatchLen
  simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]
  by_cases hf : floatMatch s > 0
  · simp only [hf, if_true]
  · simp only [hf, if_false]
    by_cases hb : binMatch s > 0
    · simp [hb]
    · by_cases hh : hexMatch s > 0
      · simp [hb, hh]
      · by_cases hd : decMatch s > 0
        · simp [hb, hh, hd]
        · by_cases ho : octMatch s > 0 <;> simp [hb, hh, hd, ho]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY PINNED / EQ-TIGHT. problem_spec_literalId s result := result = (<exact RHS>), where the RHS is built from eight OPAQUE recognisers (floatMatch, floatSuffixMatch, binMatch, hexMatch, decMatch, octMatch, intSuffixMatch, udlMatch). spec_view collapses BOTH impl and proof regions; axioms/pure/post are frozen. Any verifying impl must be provably extensionally equal to the RHS as a function of s. Because the recognisers are opaque (no properties available), no behaviorally-distinct impl can close.

SAME_SPEC: all 7 attacks == True (swebench_unified.markers.same_spec, lean backend); only the impl region (and gold proof) was edited, axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos.lean (gold, unmodified). CMD: `bash scripts/lean_verify.sh .../pos.lean` -> wrapper exit 0. #print axioms correct_literalId -> [propext, Quot.sound] (CLEAN, no sorryAx). Verified via pos_ax.lean.

### ATTACKS (each: CMD `bash scripts/lean_verify.sh .../atk_N.lean`; recorded EXIT= in out_N.txt):
- atk_1 loop-reorder oct-first (control-flow-effect): EXIT=1, residual goal `...=some (finishLiteral (decMatch s) s intSuffixMatch)` unprovable.
- atk_2 drop octal (partial-domain): EXIT=1, `ho: octMatch s>0 ⊢ False`.
- atk_3 skip float branch (partial-domain/precedence): EXIT=1, `...=some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable.
- atk_4 float branch uses intSuffixMatch instead of floatSuffixMatch (ungrounded-oracle / wrong-callee echo): EXIT=1, `some (finishLiteral (floatMatch s) s intSuffixMatch) = some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable (recognisers opaque, cannot be proved equal).
- atk_5 off-by-one baseLen (fl+1) in float branch (boundary): EXIT=1, `finishLiteral (floatMatch s + 1) ... = finishLiteral (floatMatch s) ...` unprovable.
- atk_6 integer recognisers before float branch (precedence flip, control-flow-effect): EXIT=1, `...=some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable.
- atk_prepatch the REAL BUG: keeps standard suffix but omits the udlMatch fold, emitting bare numId (drops the trailing UDL identifier, e.g. 6.62607015e-34q_J -> L6.62607015e-34E): EXIT=1, `numId (List.take (octMatch s + intSuffixMatch ...) s) = finishLiteral (octMatch s) s intSuffixMatch` unprovable. Prepatch bug reproduced.

STEP 2 (materialize + resolve): NO TRIGGER. No wrong impl closed with clean axioms, so there is no verifying-but-wrong candidate to materialize a faithful patch for; the resolve step is vacuous. patches={} accordingly.

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region declares ONLY opaque signatures (floatMatch, floatSuffixMatch, binMatch, hexMatch, decMatch, octMatch, intSuffixMatch, udlMatch) and NO `axiom … _prop` -> G-AX correctly skips; confirmed by clean #print axioms (no sorryAx). Every leg is R / A-reference / I with NO kind-3: ops 2/4/6 = R (the UDL-folding + suffix-precedence control flow, modeled structurally via finishLiteral, NOT axiomatized, per SPEC_GUIDE §3); ops 1/3 = A-reference (self.match(<regex>) recognisers, each mapped to real cfamily.py/cpp.py compiled-regex callees, appearing IDENTICALLY on spec and impl sides so they cancel in the differential); ops 5/7/8/9/10 = I (concrete numId/identId/udlId mangling formulas + none). The A-reference recogniser correspondence to the real callees holds (mapping.md 'Callee provenance'): they are the unchanged / purely-lexical prefix matchers, none leaves an output component free (result fully pinned by problem_spec).

CONCLUSION: verify => correct on this bundle. Six distinct wrong-impl classes plus the prepatch bug ALL fail to close under the fully-pinned EQ spec; positive control closes cleanly. No verify⇏correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the mangled identifier of a parsed C++ numeric literal.

A C++ literal may be written bare (e.g. `5`, `6.62607015e-34`), with a standard
numeric type suffix (e.g. `5ul`, `5.0f`), or as a *user-defined literal*: the
bare literal immediately followed by an identifier, e.g. `6.62607015e-34q_J` or
`5_udl`. The desired behaviour is that all three forms are recognised and given
a mangled identifier:

* a bare numeric literal whose source text is `data` mangles to `"L" data "E"`;
* a literal carrying a standard numeric suffix keeps the suffix as part of its
  source text, so `data` includes the suffix and the mangling is again
  `"L" data "E"`;
* a user-defined literal — a bare literal (with NO standard suffix) directly
  followed by an identifier `ident` — mangles as if it were a call of the
  identifier on the literal: `"clL_Zli" (id ident) "E" (inner) "E"`, where
  `inner` is the mangling of the underlying bare literal and `(id ident)` is the
  identifier's own mangling: the reserved namespace name `std` mangles to its
  standard abbreviation `"St"`, any other identifier to its length in decimal
  followed by its text.

A standard suffix takes precedence over a user-defined identifier: a literal that
is immediately followed by a recognised suffix is a plain suffixed literal, never
a user-defined literal. The float forms are recognised before the integer forms,
and among integer forms the binary, hexadecimal, decimal and octal shapes are
tried in that order.
-/

-- axioms-start
-- The lexical recognisers below are primitive pattern matchers over the head of
-- the input: each returns the LENGTH of the prefix it consumes (0 = no match).
-- They are modeled as opaque callees so that they appear identically in the
-- specification and the implementation; the behaviour of interest is the CONTROL
-- FLOW that combines them (when a trailing identifier is folded into a
-- user-defined literal), not the internals of any single recogniser. No property
-- of any recogniser is consumed by the proof, so no `axiom … _prop` is declared.

/-- Length of a leading floating-point literal (0 if none). -/
opaque floatMatch : List Char → Nat
/-- Length of a leading standard float type suffix following a float literal. -/
opaque floatSuffixMatch : List Char → Nat
/-- Length of a leading binary integer literal. -/
opaque binMatch : List Char → Nat
/-- Length of a leading hexadecimal integer literal. -/
opaque hexMatch : List Char → Nat
/-- Length of a leading decimal integer literal. -/
opaque decMatch : List Char → Nat
/-- Length of a leading octal integer literal. -/
opaque octMatch : List Char → Nat
/-- Length of a leading standard integer type suffix following an integer literal. -/
opaque intSuffixMatch : List Char → Nat
/-- Length of a leading user-defined-literal identifier (0 if none). -/
opaque udlMatch : List Char → Nat
-- axioms-end

-- pure-start
/-- Mangling of a bare literal whose source text is `data`. -/
def numId (data : List Char) : String := "L" ++ String.mk data ++ "E"

/-- Mangling fragment of an identifier: the reserved namespace name `std`
mangles to its standard abbreviation `"St"`; any other identifier mangles as
its length in decimal followed by its text. -/
def identId (ident : List Char) : String :=
  if ident = "std".toList then "St"
  else toString ident.length ++ String.mk ident

/-- Mangling of a user-defined literal wrapping `inner` with identifier `ident`. -/
def udlId (ident : List Char) (inner : String) : String :=
  "clL_Zli" ++ identId ident ++ "E" ++ inner ++ "E"

/-- Given a base literal occupying the first `baseLen` chars of `s` and the
suffix recogniser `suffixMatch` for that literal class, produce the mangled id:
keep a standard suffix as part of the literal's text, otherwise try to fold a
trailing identifier into a user-defined literal, otherwise emit the bare id. -/
def finishLiteral (baseLen : Nat) (s : List Char)
    (suffixMatch : List Char → Nat) : String :=
  let rest := s.drop baseLen
  let sfx := suffixMatch rest
  if sfx > 0 then
    numId (s.take (baseLen + sfx))
  else
    let baseId := numId (s.take baseLen)
    let u := udlMatch rest
    if u > 0 then udlId (rest.take u) baseId else baseId

/-- First matching integer-literal length, trying binary, hex, decimal, octal. -/
def intMatchLen (s : List Char) : Option Nat :=
  let bs := binMatch s
  if bs > 0 then some bs else
  let hs := hexMatch s
  if hs > 0 then some hs else
  let ds := decMatch s
  if ds > 0 then some ds else
  let os := octMatch s
  if os > 0 then some os else none
-- pure-end

-- post-conditions-start
/-- The mangled id of the literal at the head of `s`: a float literal (with
optional suffix or trailing user-defined identifier) if one is present, else the
first matching integer literal (likewise), else none. -/
def problem_spec_literalId (s : List Char) (result : Option String) : Prop :=
  result =
    (let fl := floatMatch s
     if fl > 0 then some (finishLiteral fl s floatSuffixMatch)
     else match intMatchLen s with
          | some il => some (finishLiteral il s intSuffixMatch)
          | none => none)
-- post-conditions-end

-- impl-start
def implementation_literalId (s : List Char) : Option String := Id.run do
  let fl := floatMatch s
  if fl > 0 then
    return some (finishLiteral fl s floatSuffixMatch)
  for m in [binMatch, hexMatch, decMatch, octMatch] do
    let il := m s
    if il > 0 then
      return some (finishLiteral il s intSuffixMatch)
  return none
-- impl-end

-- proof-start
theorem correct_literalId :
    ∀ (s : List Char),
      problem_spec_literalId s (implementation_literalId s) := by
  intro s
  unfold problem_spec_literalId implementation_literalId intMatchLen
  simp only [Id.run, List.forIn_cons, List.forIn_nil, bind, pure]
  by_cases hf : floatMatch s > 0
  · simp only [hf, if_true]
  · simp only [hf, if_false]
    by_cases hb : binMatch s > 0
    · simp [hb]
    · by_cases hh : hexMatch s > 0
      · simp [hb, hh]
      · by_cases hd : decMatch s > 0
        · simp [hb, hh, hd]
        · by_cases ho : octMatch s > 0 <;> simp [hb, hh, hd, ho]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY PINNED / EQ-TIGHT. problem_spec_literalId s result := result = (<exact RHS>), where the RHS is built from eight OPAQUE recognisers (floatMatch, floatSuffixMatch, binMatch, hexMatch, decMatch, octMatch, intSuffixMatch, udlMatch). spec_view collapses BOTH impl and proof regions; axioms/pure/post are frozen. Any verifying impl must be provably extensionally equal to the RHS as a function of s. Because the recognisers are opaque (no properties available), no behaviorally-distinct impl can close.

SAME_SPEC: all 7 attacks == True (swebench_unified.markers.same_spec, lean backend); only the impl region (and gold proof) was edited, axioms/pure/pre/post byte-identical.

POSITIVE CONTROL: pos.lean (gold, unmodified). CMD: `bash scripts/lean_verify.sh .../pos.lean` -> wrapper exit 0. #print axioms correct_literalId -> [propext, Quot.sound] (CLEAN, no sorryAx). Verified via pos_ax.lean.

### ATTACKS (each: CMD `bash scripts/lean_verify.sh .../atk_N.lean`; recorded EXIT= in out_N.txt):
- atk_1 loop-reorder oct-first (control-flow-effect): EXIT=1, residual goal `...=some (finishLiteral (decMatch s) s intSuffixMatch)` unprovable.
- atk_2 drop octal (partial-domain): EXIT=1, `ho: octMatch s>0 ⊢ False`.
- atk_3 skip float branch (partial-domain/precedence): EXIT=1, `...=some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable.
- atk_4 float branch uses intSuffixMatch instead of floatSuffixMatch (ungrounded-oracle / wrong-callee echo): EXIT=1, `some (finishLiteral (floatMatch s) s intSuffixMatch) = some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable (recognisers opaque, cannot be proved equal).
- atk_5 off-by-one baseLen (fl+1) in float branch (boundary): EXIT=1, `finishLiteral (floatMatch s + 1) ... = finishLiteral (floatMatch s) ...` unprovable.
- atk_6 integer recognisers before float branch (precedence flip, control-flow-effect): EXIT=1, `...=some (finishLiteral (floatMatch s) s floatSuffixMatch)` unprovable.
- atk_prepatch the REAL BUG: keeps standard suffix but omits the udlMatch fold, emitting bare numId (drops the trailing UDL identifier, e.g. 6.62607015e-34q_J -> L6.62607015e-34E): EXIT=1, `numId (List.take (octMatch s + intSuffixMatch ...) s) = finishLiteral (octMatch s) s intSuffixMatch` unprovable. Prepatch bug reproduced.

STEP 2 (materialize + resolve): NO TRIGGER. No wrong impl closed with clean axioms, so there is no verifying-but-wrong candidate to materialize a faithful patch for; the resolve step is vacuous. patches={} accordingly.

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region declares ONLY opaque signatures (floatMatch, floatSuffixMatch, binMatch, hexMatch, decMatch, octMatch, intSuffixMatch, udlMatch) and NO `axiom … _prop` -> G-AX correctly skips; confirmed by clean #print axioms (no sorryAx). Every leg is R / A-reference / I with NO kind-3: ops 2/4/6 = R (the UDL-folding + suffix-precedence control flow, modeled structurally via finishLiteral, NOT axiomatized, per SPEC_GUIDE §3); ops 1/3 = A-reference (self.match(<regex>) recognisers, each mapped to real cfamily.py/cpp.py compiled-regex callees, appearing IDENTICALLY on spec and impl sides so they cancel in the differential); ops 5/7/8/9/10 = I (concrete numId/identId/udlId mangling formulas + none). The A-reference recogniser correspondence to the real callees holds (mapping.md 'Callee provenance'): they are the unchanged / purely-lexical prefix matchers, none leaves an output component free (result fully pinned by problem_spec).

CONCLUSION: verify => correct on this bundle. Six distinct wrong-impl classes plus the prepatch bug ALL fail to close under the fully-pinned EQ spec; positive control closes cleanly. No verify⇏correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / model-vs-real-callee drift) — NO divergence found. Modeled function: numeric-literal id computation of the POST-PATCH DefinitionParser._parse_literal (sphinx/domains/cpp.py). Drove the REAL parser at base_commit 2e506c5a + gold patch (worktree) via DefinitionParser(s)._parse_literal().get_id and diffed against an op-for-op replica of Solution.lean's implementation_literalId.

RESULTS: (1) Curated corpus incl. issue repro '6.62607015e-34q_J', '5_udl','5uludl','5lll','5l','5std'(->St abbrev),'5stdx','0xApF_udl', suffix-precedence, bare/none cases = 0 mismatches (real==model on every case). (2) Random fuzz over C++-literal alphabet, 1M+ inputs (seeds 7590 and 99): 0 mismatches once leading-ASCII-space inputs are excluded.

All ~3600 raw fuzz divergences share EXACTLY one cause: a leading space. The real _parse_literal calls self.skip_ws() (and the nullptr/true/false skip_word checks) BEFORE 'pos = self.pos'; the model takes s as the head AFTER that preprocessing (mapping.md bijection: s <-> self.definition[self.pos:], the unparsed head). After skip_ws the head never begins with whitespace, so leading-space strings are outside the modeled domain — legitimate scoping, not spec drift. String/char literal branches are likewise explicitly scoped out (numeric-only bundle) and never reached on a numeric head. The suffix-takes-precedence-over-UDL control flow, float-before-int + bin/hex/dec/oct ordering, and the three get_id mangling formulas (numId, identId incl. std->St, udlId) all match the real code exactly.

STRUCTURAL CHECKS: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True (spec region byte-identical; only impl/proof differ). lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). '#print axioms correct_literalId' -> [propext, Quot.sound]: clean, no sorryAx, honest proof. G-AX legitimately skips (recognisers are A-references identical in spec and impl, no consumed axiom … _prop). No input found where the spec disagrees with the real repo behavior on the modeled numeric-literal domain. Spec is FAITHFUL (neither too strong nor drifting).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction judgment for lean bundle sphinx-doc__sphinx-7590.

Public problem_statement already discloses: the bug is 'C++ User Defined Literals not supported', the exact repro `6.62607015e-34q_J`, the target file sphinx/domains/cpp.py, and an explicit request to add UDL support.

Mechanical G-LEAK screen: PASS (no hard failures). Verified by running leakage.screen over spec_view: no diff markers, no patched file path/module, no narration, and no spec-view identifier or comment echoes any patched repo symbol (changed symbols = ASTUserDefinedLiteral, describe_signature, get_id, parse_literal, stringify — none appear in the view; model uses abstract names numId/identId/udlId/finishLiteral/floatMatch/udlMatch/problem_spec_literalId).

Semantic reconstruction analysis (beyond the lexical screen):
- The docstring describes the DESIRED contract (recognise bare / standard-suffix / user-defined numeric literals and produce their mangled id). This is exactly the behavior the public task requests ('add those [UDL] features'); specifying the target contract is the spec's job, not edit-localization beyond what problem_statement already reveals.
- The three mangling formulas ("L"+data+"E", clL_Zli{ident}E{inner}E, std->'St', else len+text) are the standard C++ Itanium ABI mangling conventions required to pin correctness; they are not diff-specific gold reconstruction.
- Suffix-takes-precedence and the float-before-integer / bin,hex,dec,oct ordering are properties of the C++ language / recogniser set, not a disclosure of which side is the gold edit.
- Crucially, the spec regions (docstring, opaque signatures, pure defs, post-conditions) are BYTE-IDENTICAL between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True). The discriminating gold decision (folding a trailing identifier via udlMatch into a UDL vs. dropping it) lives ENTIRELY in the elided impl/proof regions, which are NOT part of the spec view. A solver reading the spec view cannot tell the gold edit from the pre-patch buggy behavior — the view is symmetric across the fix.

Not a relaxed bundle (relaxed_leakage: None, no RELAXED_LEAKAGE.md), so no panel_3 deferral applies. The spec view faithfully states the behavior the public task asks for, using abstract names, without exposing diff structure or the discriminating edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
