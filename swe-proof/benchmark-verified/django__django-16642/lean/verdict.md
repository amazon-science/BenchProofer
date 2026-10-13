# P2 adversarial audit — django__django-16642

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,17 +55,13 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
+/-- Prepatch: omit the br and compress override keys. -/
 def implementation_contentType (contentType encoding : Option String) : String := Id.run do
   let mut ct := contentType
   if let some e := encoding then
-    if e = "br" then ct := some "application/x-brotli"
-    else if e = "bzip2" then ct := some "application/x-bzip"
-    else if e = "compress" then ct := some "application/x-compress"
+    if e = "bzip2" then ct := some "application/x-bzip"
     else if e = "gzip" then ct := some "application/gzip"
     else if e = "xz" then ct := some "application/x-xz"
   match ct with
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,9 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
+/-- Partial-domain: omit the xz override key. -/
 def implementation_contentType (contentType encoding : Option String) : String := Id.run do
   let mut ct := contentType
   if let some e := encoding then
@@ -67,7 +65,6 @@
     else if e = "bzip2" then ct := some "application/x-bzip"
     else if e = "compress" then ct := some "application/x-compress"
     else if e = "gzip" then ct := some "application/gzip"
-    else if e = "xz" then ct := some "application/x-xz"
   match ct with
   | some s => return (if s.isEmpty then "application/octet-stream" else s)
   | none => return "application/octet-stream"
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,9 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
+/-- Boundary: drop the isEmpty fallback; a some "" returns "" verbatim. -/
 def implementation_contentType (contentType encoding : Option String) : String := Id.run do
   let mut ct := contentType
   if let some e := encoding then
@@ -69,7 +67,7 @@
     else if e = "gzip" then ct := some "application/gzip"
     else if e = "xz" then ct := some "application/x-xz"
   match ct with
-  | some s => return (if s.isEmpty then "application/octet-stream" else s)
+  | some s => return s
   | none => return "application/octet-stream"
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,22 +55,14 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
+/-- Control-flow-effect: unconditionally return the generic binary media type. -/
 def implementation_contentType (contentType encoding : Option String) : String := Id.run do
-  let mut ct := contentType
-  if let some e := encoding then
-    if e = "br" then ct := some "application/x-brotli"
-    else if e = "bzip2" then ct := some "application/x-bzip"
-    else if e = "compress" then ct := some "application/x-compress"
-    else if e = "gzip" then ct := some "application/gzip"
-    else if e = "xz" then ct := some "application/x-xz"
-  match ct with
-  | some s => return (if s.isEmpty then "application/octet-stream" else s)
-  | none => return "application/octet-stream"
+  let mut _ct := contentType
+  if let some _e := encoding then
+    _ct := contentType
+  return "application/octet-stream"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,22 +55,11 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
-def implementation_contentType (contentType encoding : Option String) : String := Id.run do
-  let mut ct := contentType
-  if let some e := encoding then
-    if e = "br" then ct := some "application/x-brotli"
-    else if e = "bzip2" then ct := some "application/x-bzip"
-    else if e = "compress" then ct := some "application/x-compress"
-    else if e = "gzip" then ct := some "application/gzip"
-    else if e = "xz" then ct := some "application/x-xz"
-  match ct with
-  | some s => return (if s.isEmpty then "application/octet-stream" else s)
-  | none => return "application/octet-stream"
+/-- Ungrounded-oracle echo: defer to the spec function verbatim. -/
+def implementation_contentType (contentType encoding : Option String) : String :=
+  finalContentType contentType encoding
 -- impl-end
 
 -- proof-start
@@ -79,21 +68,5 @@
     problem_spec_contentType contentType encoding
       (implementation_contentType contentType encoding) := by
   intro contentType encoding
-  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType
-  cases encoding with
-  | none => cases contentType <;> rfl
-  | some e =>
-    simp only [Id.run, bind, pure]
-    by_cases hbr : e = "br"
-    · subst hbr; rfl
-    by_cases hbz : e = "bzip2"
-    · subst hbz; rfl
-    by_cases hco : e = "compress"
-    · subst hco; rfl
-    by_cases hgz : e = "gzip"
-    · subst hgz; rfl
-    by_cases hxz : e = "xz"
-    · subst hxz; rfl
-    · simp only [hbr, hbz, hco, hgz, hxz, if_false]
-      cases contentType <;> rfl
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,15 +55,13 @@
   result = finalContentType contentType encoding
 -- post-conditions-end
 
+
 -- impl-start
-/-- Start from the guessed type and, when the encoding is a recognized
-compression scheme, replace it with that scheme's dedicated media type; finally
-substitute the generic binary media type whenever the selection is absent or
-empty. -/
+/-- Swap: map br to application/gzip instead of application/x-brotli. -/
 def implementation_contentType (contentType encoding : Option String) : String := Id.run do
   let mut ct := contentType
   if let some e := encoding then
-    if e = "br" then ct := some "application/x-brotli"
+    if e = "br" then ct := some "application/gzip"
     else if e = "bzip2" then ct := some "application/x-bzip"
     else if e = "compress" then ct := some "application/x-compress"
     else if e = "gzip" then ct := some "application/gzip"
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification is the selection of a response content type from a guessed
-- (type, compression-encoding) pair; it is modeled DEEPLY (the concrete
-- encoding→type association plus the absent/empty fallback below) rather than
-- abstracted behind any callee. The routine that produces the guessed pair from
-- a name sits at the input boundary (it supplies the two arguments) and is not
-- part of the modeled computation. The proof agent may add `_prop` axioms only
-- if it gets stuck.
-- axioms-end

-- pure-start
/-- The content type associated with a known compression encoding. For every
recognized compression scheme this is the encoding's own dedicated media type
(so that the payload is described as the compressed archive it actually is,
rather than as the underlying file); any other encoding has no associated
override. Grounded entirely in the encoding string. -/
def encodingContentType (e : String) : Option String :=
  if e = "br" then some "application/x-brotli"
  else if e = "bzip2" then some "application/x-bzip"
  else if e = "compress" then some "application/x-compress"
  else if e = "gzip" then some "application/gzip"
  else if e = "xz" then some "application/x-xz"
  else none

/-- The final content type chosen for a guessed `(contentType, encoding)` pair.
When the encoding is a known compression scheme, its dedicated media type takes
precedence over the guessed type; otherwise the guessed type is used. In all
cases an absent or empty result is replaced by the generic binary media type.
Grounded entirely in the two input components. -/
def finalContentType (contentType encoding : Option String) : String :=
  let overridden : Option String :=
    match encoding with
    | none => contentType
    | some e =>
        match encodingContentType e with
        | some v => some v
        | none => contentType
  match overridden with
  | some s => if s.isEmpty then "application/octet-stream" else s
  | none => "application/octet-stream"
-- pure-end

-- post-conditions-start
/-- The resulting content type is exactly the type selected for the guessed
`(contentType, encoding)` pair: a known compression encoding's dedicated media
type overrides the guessed type, an unrecognized or absent encoding keeps the
guessed type, and an absent or empty selection falls back to the generic binary
media type. -/
def problem_spec_contentType
    (contentType encoding : Option String) (result : String) : Prop :=
  result = finalContentType contentType encoding
-- post-conditions-end

-- impl-start
/-- Start from the guessed type and, when the encoding is a recognized
compression scheme, replace it with that scheme's dedicated media type; finally
substitute the generic binary media type whenever the selection is absent or
empty. -/
def implementation_contentType (contentType encoding : Option String) : String := Id.run do
  let mut ct := contentType
  if let some e := encoding then
    if e = "br" then ct := some "application/x-brotli"
    else if e = "bzip2" then ct := some "application/x-bzip"
    else if e = "compress" then ct := some "application/x-compress"
    else if e = "gzip" then ct := some "application/gzip"
    else if e = "xz" then ct := some "application/x-xz"
  match ct with
  | some s => return (if s.isEmpty then "application/octet-stream" else s)
  | none => return "application/octet-stream"
-- impl-end

-- proof-start
theorem correct_contentType :
    ∀ (contentType encoding : Option String),
    problem_spec_contentType contentType encoding
      (implementation_contentType contentType encoding) := by
  intro contentType encoding
  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType
  cases encoding with
  | none => cases contentType <;> rfl
  | some e =>
    simp only [Id.run, bind, pure]
    by_cases hbr : e = "br"
    · subst hbr; rfl
    by_cases hbz : e = "bzip2"
    · subst hbz; rfl
    by_cases hco : e = "compress"
    · subst hco; rfl
    by_cases hgz : e = "gzip"
    · subst hgz; rfl
    by_cases hxz : e = "xz"
    · subst hxz; rfl
    · simp only [hbr, hbz, hco, hgz, hxz, if_false]
      cases contentType <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional equality — problem_spec_contentType c e r := (r = finalContentType c e) — over an EMPTY axioms region (meta: deep_model_references=[], opaque_callees=[], axioms-start/end body is only comments). No A-legs exist to attack; the CHANGED op (the encoding->media-type override dict, post-patch key set {br,bzip2,compress,gzip,xz}) is modeled DEEPLY by encodingContentType, not axiomatized. So a falsification would require a behaviorally-wrong impl whose gold proof still closes.

same_spec: all 6 attacks byte-identical spec (True), confirmed via swebench_unified.markers.same_spec against Solution.lean.

### COMMANDS (project root; ran concurrently, <=4 at a time):
  bash scripts/lean_verify.sh atk_N.lean
### Results
  atk_1 prepatch bug (omit br,compress keys)   -> exit 1 REJECTED
  atk_2 partial-domain (omit xz key)           -> exit 1 REJECTED
  atk_3 boundary (drop isEmpty->octet fallback)-> exit 1 REJECTED
  atk_4 control-flow-effect (always octet)     -> exit 1 REJECTED
  atk_5 ungrounded-oracle echo (=finalContentType, rfl proof) -> exit 0 VERIFIES; #print axioms correct_contentType => 'does not depend on any axioms' (clean)
  atk_6 swap (br -> application/gzip)          -> exit 1 REJECTED
  pos_control (gold Solution.lean)             -> exit 0 VERIFIES

MANDATORY RESOLVE (every closing clean-axiom attack): only atk_5 closes. Its faithful refined patch = the gold patch (echo returns finalContentType verbatim, which models exactly the post-patch content_type = {br,bzip2,compress,gzip,xz}.get(encoding, content_type) or 'application/octet-stream'). Executed run_resolve('django__django-16642', <that patch>, timeout=1800) => ResolveResult.resolved=True, note='resolved'. RESOLVES => not a spec weakness (consistent with post-2026-08-06 G-PANEL-1 echo policy: a same-spec verifying attack whose refined patch RESOLVES is not a defect).

No attack exhibits verify-but-not-resolve, so verify=>correct is NOT violated. All wrong behaviors (5 of 6) are rejected by the exact-equality spec exactly as required.

REFINEMENT AUDIT: 5 legs tagged R / I / I / R / R — all kind R or I, NO kind-3 (changed-inexpressible). No A-consumed / A-reference rows; axioms region empty by design and G-AX is a skip stub. mimetypes.guess_type correctly classified as an input-boundary producer, not a modeled callee. Correspondence (dict/.get/or <-> if-chain + isEmpty/none fallback, str<->some / None<->none / ''-and-None-falsy bijection) holds. conformance_check.py present, conf_skip=false. mapping.md consistent.

VERDICT SOUND: >=6 distinct attacks encoded and verified; every behaviorally-wrong impl rejected; the sole verifying attack (echo) has a materialized faithful patch that was resolve-run and RESOLVES.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification is the selection of a response content type from a guessed
-- (type, compression-encoding) pair; it is modeled DEEPLY (the concrete
-- encoding→type association plus the absent/empty fallback below) rather than
-- abstracted behind any callee. The routine that produces the guessed pair from
-- a name sits at the input boundary (it supplies the two arguments) and is not
-- part of the modeled computation. The proof agent may add `_prop` axioms only
-- if it gets stuck.
-- axioms-end

-- pure-start
/-- The content type associated with a known compression encoding. For every
recognized compression scheme this is the encoding's own dedicated media type
(so that the payload is described as the compressed archive it actually is,
rather than as the underlying file); any other encoding has no associated
override. Grounded entirely in the encoding string. -/
def encodingContentType (e : String) : Option String :=
  if e = "br" then some "application/x-brotli"
  else if e = "bzip2" then some "application/x-bzip"
  else if e = "compress" then some "application/x-compress"
  else if e = "gzip" then some "application/gzip"
  else if e = "xz" then some "application/x-xz"
  else none

/-- The final content type chosen for a guessed `(contentType, encoding)` pair.
When the encoding is a known compression scheme, its dedicated media type takes
precedence over the guessed type; otherwise the guessed type is used. In all
cases an absent or empty result is replaced by the generic binary media type.
Grounded entirely in the two input components. -/
def finalContentType (contentType encoding : Option String) : String :=
  let overridden : Option String :=
    match encoding with
    | none => contentType
    | some e =>
        match encodingContentType e with
        | some v => some v
        | none => contentType
  match overridden with
  | some s => if s.isEmpty then "application/octet-stream" else s
  | none => "application/octet-stream"
-- pure-end

-- post-conditions-start
/-- The resulting content type is exactly the type selected for the guessed
`(contentType, encoding)` pair: a known compression encoding's dedicated media
type overrides the guessed type, an unrecognized or absent encoding keeps the
guessed type, and an absent or empty selection falls back to the generic binary
media type. -/
def problem_spec_contentType
    (contentType encoding : Option String) (result : String) : Prop :=
  result = finalContentType contentType encoding
-- post-conditions-end

-- impl-start
/-- Start from the guessed type and, when the encoding is a recognized
compression scheme, replace it with that scheme's dedicated media type; finally
substitute the generic binary media type whenever the selection is absent or
empty. -/
def implementation_contentType (contentType encoding : Option String) : String := Id.run do
  let mut ct := contentType
  if let some e := encoding then
    if e = "br" then ct := some "application/x-brotli"
    else if e = "bzip2" then ct := some "application/x-bzip"
    else if e = "compress" then ct := some "application/x-compress"
    else if e = "gzip" then ct := some "application/gzip"
    else if e = "xz" then ct := some "application/x-xz"
  match ct with
  | some s => return (if s.isEmpty then "application/octet-stream" else s)
  | none => return "application/octet-stream"
-- impl-end

-- proof-start
theorem correct_contentType :
    ∀ (contentType encoding : Option String),
    problem_spec_contentType contentType encoding
      (implementation_contentType contentType encoding) := by
  intro contentType encoding
  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType
  cases encoding with
  | none => cases contentType <;> rfl
  | some e =>
    simp only [Id.run, bind, pure]
    by_cases hbr : e = "br"
    · subst hbr; rfl
    by_cases hbz : e = "bzip2"
    · subst hbz; rfl
    by_cases hco : e = "compress"
    · subst hco; rfl
    by_cases hgz : e = "gzip"
    · subst hgz; rfl
    by_cases hxz : e = "xz"
    · subst hxz; rfl
    · simp only [hbr, hbz, hco, hgz, hxz, if_false]
      cases contentType <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: exact functional equality — problem_spec_contentType c e r := (r = finalContentType c e) — over an EMPTY axioms region (meta: deep_model_references=[], opaque_callees=[], axioms-start/end body is only comments). No A-legs exist to attack; the CHANGED op (the encoding->media-type override dict, post-patch key set {br,bzip2,compress,gzip,xz}) is modeled DEEPLY by encodingContentType, not axiomatized. So a falsification would require a behaviorally-wrong impl whose gold proof still closes.

same_spec: all 6 attacks byte-identical spec (True), confirmed via swebench_unified.markers.same_spec against Solution.lean.

### COMMANDS (project root; ran concurrently, <=4 at a time):
  bash scripts/lean_verify.sh atk_N.lean
### Results
  atk_1 prepatch bug (omit br,compress keys)   -> exit 1 REJECTED
  atk_2 partial-domain (omit xz key)           -> exit 1 REJECTED
  atk_3 boundary (drop isEmpty->octet fallback)-> exit 1 REJECTED
  atk_4 control-flow-effect (always octet)     -> exit 1 REJECTED
  atk_5 ungrounded-oracle echo (=finalContentType, rfl proof) -> exit 0 VERIFIES; #print axioms correct_contentType => 'does not depend on any axioms' (clean)
  atk_6 swap (br -> application/gzip)          -> exit 1 REJECTED
  pos_control (gold Solution.lean)             -> exit 0 VERIFIES

MANDATORY RESOLVE (every closing clean-axiom attack): only atk_5 closes. Its faithful refined patch = the gold patch (echo returns finalContentType verbatim, which models exactly the post-patch content_type = {br,bzip2,compress,gzip,xz}.get(encoding, content_type) or 'application/octet-stream'). Executed run_resolve('django__django-16642', <that patch>, timeout=1800) => ResolveResult.resolved=True, note='resolved'. RESOLVES => not a spec weakness (consistent with post-2026-08-06 G-PANEL-1 echo policy: a same-spec verifying attack whose refined patch RESOLVES is not a defect).

No attack exhibits verify-but-not-resolve, so verify=>correct is NOT violated. All wrong behaviors (5 of 6) are rejected by the exact-equality spec exactly as required.

REFINEMENT AUDIT: 5 legs tagged R / I / I / R / R — all kind R or I, NO kind-3 (changed-inexpressible). No A-consumed / A-reference rows; axioms region empty by design and G-AX is a skip stub. mimetypes.guess_type correctly classified as an input-boundary producer, not a modeled callee. Correspondence (dict/.get/or <-> if-chain + isEmpty/none fallback, str<->some / None<->none / ''-and-None-falsy bijection) holds. conformance_check.py present, conf_skip=false. mapping.md consistent.

VERDICT SOUND: >=6 distinct attacks encoded and verified; every behaviorally-wrong impl rejected; the sole verifying attack (echo) has a materialized faithful patch that was resolve-run and RESOLVES.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: FAITHFUL — no diverging input found. Modeled function finalContentType(contentType, encoding) faithfully mirrors the post-patch Python block in FileResponse.set_headers (django/http/response.py:611-618 @ base_commit): content_type = {br,bzip2,compress,gzip,xz}.get(encoding, content_type); Content-Type = content_type or 'application/octet-stream'. Verified point-by-point: (1) encodingContentType maps br->application/x-brotli, bzip2->application/x-bzip, compress->application/x-compress, gzip->application/gzip, xz->application/x-xz — BYTE-EXACT vs the gold patch (checked test.jsonl gold patch = adds exactly 'br' and 'compress' keys) and vs the base response.py dict. (2) .get default (encoding None/unrecognized keeps contentType) matches the none/none Lean branches. (3) The 'or fallback' — Python falsy str is exactly None and '' — matches Lean none->octet, some ''->octet (via isEmpty), some s (s!='')->s. Whitespace ' ' is truthy in both. Override dict values are all non-empty, so they never hit the fallback in either. No over-constraint: spec is a total equality over all (Option String, Option String) inputs, exactly the range mimetypes.guess_type boundary can yield. Independent verification: (a) same_spec(Solution, Solution_prepatch) = True via swebench_unified.markers with LeanBackend.language — spec region frozen/byte-identical. (b) Lean compiles exit 0; #print axioms correct_contentType = [propext] only — NO sorryAx, proof is genuine. (c) conformance_check.py differential: 120015 inputs, 0 disagreements against an independent oracle using real Python dict + truthiness (incl. None/''/BR/deflate/whitespace cases). No modeled callee is abstracted (axioms region empty, G-AX skip); mimetypes.guess_type is correctly treated as an input-boundary producer, not part of the modeled computation. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity verified: markers.spec_view(Solution.lean, lean) hashes to e1160bf079b53e41ccb304dbc792e922adf066a20fb75856d7a983d7a4c68e69, byte-identical to meta.json region_hashes.spec_view; impl and proof regions correctly elided. Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file path django/http/response.py, no identifier/comment echoing a patched symbol, no narration); bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md).

Gold edit adds two dict entries: 'br'->'application/x-brotli' and 'compress'->'application/x-compress'. Public problem_statement names only the br/Z extensions producing text/html; it discloses NO media-type target strings, NO 'compress' encoding, NO dict/.get mechanism, NO pre-patch baseline.

Reconstruction analysis: the spec view (encodingContentType 5-key table br/bzip2/compress/gzip/xz, finalContentType, problem_spec_contentType) encodes the CORRECTED observable contract, which is the definition of a bugfix postcondition and is what G-DIFF exercises (Solution_prepatch.lean fails against it) -- intended, not leakage. The x-brotli/x-compress strings are the observable Content-Type OUTPUT that the hidden F2P test asserts; a spec transliterating that public-API output is the correct artifact, not a leaked secret. Crucially the spec view does NOT reveal the gold DELTA: all five encodings are shown uniformly with no marking of new (br,compress) vs pre-existing (bzip2,gzip,xz), the pre-patch dict {bzip2,gzip,xz} appears nowhere, and no file path/line-numbers/.get mechanism appears -- so the edit boundary cannot be reconstructed from the spec alone beyond the already-public 'br/Z are broken'. No line in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
