# P2 adversarial audit — django__django-16642

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TOTAL functional equality with no precondition (ensures out = resolvedMediaType guessed encoding), so any verifying impl must equal the frozen reference (which already contains the br+compress keys) on the entire input domain. No verifying wrong-impl exists; the only additional verifying impl (echo, atk_5) is semantically the gold patch and RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,12 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
+    let chosen :=
+      (match encoding with
+       | some "bzip2" => some "application/x-bzip"
+       | some "gzip"  => some "application/gzip"
+       | some "xz"    => some "application/x-xz"
+       | _            => none).orElse (fun _ => guessed)
     return chosen.getD "application/octet-stream"
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,7 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
-    return chosen.getD "application/octet-stream"
+    return guessed.getD "application/octet-stream"
     -- impl-end
 
 prove_correct resolveMediaType by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,14 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
+    let chosen :=
+      (match encoding with
+       | some "br"       => some "application/x-bzip"
+       | some "bzip2"    => some "application/x-bzip"
+       | some "compress" => some "application/x-compress"
+       | some "gzip"     => some "application/gzip"
+       | some "xz"       => some "application/x-xz"
+       | _               => none).orElse (fun _ => guessed)
     return chosen.getD "application/octet-stream"
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
+    let chosen := guessed.orElse (fun _ => compressionMediaType encoding)
     return chosen.getD "application/octet-stream"
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,13 +67,8 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
-    return chosen.getD "application/octet-stream"
+    return resolvedMediaType guessed encoding
     -- impl-end
 
 prove_correct resolveMediaType by
   loom_solve
-  simp [resolvedMediaType]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,7 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
-    return chosen.getD "application/octet-stream"
+    return "application/octet-stream"
     -- impl-end
 
 prove_correct resolveMediaType by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,13 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
-    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
+    let chosen :=
+      (match encoding with
+       | some "bzip2"    => some "application/x-bzip"
+       | some "compress" => some "application/x-compress"
+       | some "gzip"     => some "application/gzip"
+       | some "xz"       => some "application/x-xz"
+       | _               => none).orElse (fun _ => guessed)
     return chosen.getD "application/octet-stream"
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,11 +67,8 @@
   ensures out = resolvedMediaType guessed encoding
   do
     -- impl-start
-    -- A recognised compression label contributes its dedicated media type;
-    -- otherwise fall back to the guessed media type.
     let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
-    -- ... and to the generic binary media type when even that is absent.
-    return chosen.getD "application/octet-stream"
+    return chosen.getD "text/plain"
     -- impl-end
 
 prove_correct resolveMediaType by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two carrier values this operation consumes — the
--  guessed media type and the compression-encoding label — are produced by an
--  unchanged upstream type-sniffer that is shared, untouched, by every branch;
--  its outputs are taken directly as the inputs of the modeled function
--  (provenance in mapping.md §3), so there is no outside contract for the proof
--  to consume and no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The dedicated media type for a compression encoding label. When a file's name
   advertises a compression scheme, the response must announce that scheme's own
   media type rather than the media type of the wrapped (uncompressed) payload,
   so that a client does not silently inflate the bytes. Each recognised
   compression label has exactly one dedicated media type; an unrecognised or
   absent label (`none`) has none (`none`), and the wrapped payload's type is
   used instead (see `resolvedMediaType`). -/
def compressionMediaType (encoding : Option String) : Option String :=
  match encoding with
  | some "br"       => some "application/x-brotli"
  | some "bzip2"    => some "application/x-bzip"
  | some "compress" => some "application/x-compress"
  | some "gzip"     => some "application/gzip"
  | some "xz"       => some "application/x-xz"
  | _               => none

/- The media type announced for a payload, given the type guessed for its name
   (`guessed`) and any compression-encoding label (`encoding`). A recognised
   compression label wins and contributes its dedicated media type; otherwise
   the guessed type is used; and when neither is available the generic binary
   media type `application/octet-stream` is the fallback. -/
def resolvedMediaType (guessed encoding : Option String) : String :=
  (compressionMediaType encoding |>.orElse (fun _ => guessed)).getD
    "application/octet-stream"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the media type to announce for a payload from two read-only inputs:
   the media type guessed for the payload's name (`guessed`, absent as `none`)
   and the payload's compression-encoding label (`encoding`, absent as `none`).

   Desired behaviour: when the name advertises a recognised compression scheme,
   the announced media type is that scheme's OWN dedicated media type — never the
   media type of the wrapped, uncompressed payload — so a client is not led to
   transparently decompress it. When there is no recognised compression scheme,
   the guessed media type is announced; and when even that is absent, the generic
   binary media type is announced. The result is therefore always a present
   (non-absent) media type.

   Both inputs are read-only and neither is declared `mut` (directive 5): the
   resolution only reads the guess and the encoding label, mutating nothing. -/
method resolveMediaType (guessed : Option String) (encoding : Option String)
    return (out : String)
  ensures out = resolvedMediaType guessed encoding
  do
    -- impl-start
    -- A recognised compression label contributes its dedicated media type;
    -- otherwise fall back to the guessed media type.
    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
    -- ... and to the generic binary media type when even that is absent.
    return chosen.getD "application/octet-stream"
    -- impl-end

prove_correct resolveMediaType by
  loom_solve
  simp [resolvedMediaType]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol summary

SAME-SPEC: confirmed True for all 8 attacks + pos_control via swebench_unified.markers.same_spec (velvet backend). Only impl region + prove_correct body vary; axioms/pure(compressionMediaType,resolvedMediaType)/pre/post are byte-identical (frozen).

SPEC SHAPE: `method resolveMediaType ... ensures out = resolvedMediaType guessed encoding` — a TOTAL (loom.semantics.termination total) functional equality with NO precondition. Verify => impl computes resolvedMediaType on the ENTIRE domain. This is the tightest possible spec shape; the discriminating changed op (the 5-key compression table incl. the NEW br+compress keys) is modeled DEEPLY/CONCRETELY in the FROZEN pure region, not behind an axiom. There are NO A-legs and NO deep-model references to attack (meta.json axioms=[], deep_model_references=[]).

VERIFY COMMAND (each): `bash scripts/lean_verify.sh <file>` run from project root, concurrently in batches of 4.
### Results
- pos_control.lean (gold impl): EXIT 0 = VERIFIES.
- atk_1.lean (prepatch bug: 3-key table omitting br+compress; partial-domain): EXIT 1, genuine `unsolved goals` on the br/compress cases. PREPATCH REPRODUCED.
- atk_2.lean (ignore compression, guessed then default; partial-domain): EXIT 1, unsolved goals.
- atk_3.lean (value-swap: br -> application/x-bzip; boundary/value corruption): EXIT 1, unsolved goals.
- atk_4.lean (wrong precedence: guessed.orElse compression; control-flow-effect): EXIT 1, unsolved goals.
- atk_5.lean (ungrounded-oracle ECHO: `return resolvedMediaType guessed encoding`): initially EXIT 3-style artifact `No goals to be solved` at the redundant `simp` line — a PROOF-SCRIPT artifact, not semantic. Removed the redundant `simp [resolvedMediaType]` line (proof body is in the mutable region, still same_spec True) -> EXIT 0 = VERIFIES.
- atk_6.lean (constant application/octet-stream): EXIT 1, unsolved goals.
- atk_7.lean (omit only NEW br key, keep compress; partial boundary): EXIT 1, unsolved goals.
- atk_8.lean (wrong fallback default text/plain): EXIT 1, unsolved goals.

KEY DISTINCTION: all 7 wrong impls fail with GENUINE `unsolved goals` (real semantic mismatch — no proof-strengthening can rescue them because the total equality is literally false for them). atk_5 failed only with `No goals to be solved` (redundant tactic), which a real adversary trivially fixes; once fixed it verifies. This is the ONLY verifying impl besides gold, and it is semantically identical to the reference.

RESOLVE RUN (mandatory for every verifying impl): atk_5's faithful refined patch is byte-identical to the gold patch (the echo computes resolvedMediaType = full 5-key table incl br+compress). Ran via swebench_unified.harness.run_resolve('django__django-16642', <atk_5.patch>): RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the sole verifying wrong-shaped candidate RESOLVES => it does NOT break the spec (a resolving echo of the gold is not a weakness, per G-EQ / G-PANEL-1 resolve policy).

REFINEMENT.MD AUDIT: legs A1..A6 are all R or I (A3 is I: frozen compressionMediaType 5-key match transliterates the post-patch dict key-for-key; A1/A2 R input-provenance to unchanged mimetypes.guess_type, matching meta.json input_provenance; A4 R+I orElse<->dict.get; A5 R getD<->`x or default`; A6 R result<->header). NO kind-3 legs. NO A-consumed / A-reference legs exist (no axioms, no deep-model refs); G-AX correctly vacuous. Model<->patch correspondence holds: the two ADDED dict keys (br, compress) are present in the frozen compressionMediaType table, and G-CONF (recorded) confirmed the R/I shadow == real patched FileResponse Content-Type over 100017 fuzzed names (seed 16642), 0 disagreements.

CONCLUSION: verify => impl == frozen reference (total equality, no precondition) => faithful patch is behaviorally the gold patch => resolves. No verify-but-not-resolve gap possible. >=5 distinct attack families run (partial-domain x3, boundary/value x2, control-flow-effect, echo, constant), none breaks the spec; positive control verifies; the one verifying candidate's materialized patch was executed through the official harness and RESOLVED. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TOTAL functional equality with no precondition (ensures out = resolvedMediaType guessed encoding), so any verifying impl must equal the frozen reference (which already contains the br+compress keys) on the entire input domain. No verifying wrong-impl exists; the only additional verifying impl (echo, atk_5) is semantically the gold patch and RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two carrier values this operation consumes — the
--  guessed media type and the compression-encoding label — are produced by an
--  unchanged upstream type-sniffer that is shared, untouched, by every branch;
--  its outputs are taken directly as the inputs of the modeled function
--  (provenance in mapping.md §3), so there is no outside contract for the proof
--  to consume and no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The dedicated media type for a compression encoding label. When a file's name
   advertises a compression scheme, the response must announce that scheme's own
   media type rather than the media type of the wrapped (uncompressed) payload,
   so that a client does not silently inflate the bytes. Each recognised
   compression label has exactly one dedicated media type; an unrecognised or
   absent label (`none`) has none (`none`), and the wrapped payload's type is
   used instead (see `resolvedMediaType`). -/
def compressionMediaType (encoding : Option String) : Option String :=
  match encoding with
  | some "br"       => some "application/x-brotli"
  | some "bzip2"    => some "application/x-bzip"
  | some "compress" => some "application/x-compress"
  | some "gzip"     => some "application/gzip"
  | some "xz"       => some "application/x-xz"
  | _               => none

/- The media type announced for a payload, given the type guessed for its name
   (`guessed`) and any compression-encoding label (`encoding`). A recognised
   compression label wins and contributes its dedicated media type; otherwise
   the guessed type is used; and when neither is available the generic binary
   media type `application/octet-stream` is the fallback. -/
def resolvedMediaType (guessed encoding : Option String) : String :=
  (compressionMediaType encoding |>.orElse (fun _ => guessed)).getD
    "application/octet-stream"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the media type to announce for a payload from two read-only inputs:
   the media type guessed for the payload's name (`guessed`, absent as `none`)
   and the payload's compression-encoding label (`encoding`, absent as `none`).

   Desired behaviour: when the name advertises a recognised compression scheme,
   the announced media type is that scheme's OWN dedicated media type — never the
   media type of the wrapped, uncompressed payload — so a client is not led to
   transparently decompress it. When there is no recognised compression scheme,
   the guessed media type is announced; and when even that is absent, the generic
   binary media type is announced. The result is therefore always a present
   (non-absent) media type.

   Both inputs are read-only and neither is declared `mut` (directive 5): the
   resolution only reads the guess and the encoding label, mutating nothing. -/
method resolveMediaType (guessed : Option String) (encoding : Option String)
    return (out : String)
  ensures out = resolvedMediaType guessed encoding
  do
    -- impl-start
    -- A recognised compression label contributes its dedicated media type;
    -- otherwise fall back to the guessed media type.
    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)
    -- ... and to the generic binary media type when even that is absent.
    return chosen.getD "application/octet-stream"
    -- impl-end

prove_correct resolveMediaType by
  loom_solve
  simp [resolvedMediaType]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol summary

SAME-SPEC: confirmed True for all 8 attacks + pos_control via swebench_unified.markers.same_spec (velvet backend). Only impl region + prove_correct body vary; axioms/pure(compressionMediaType,resolvedMediaType)/pre/post are byte-identical (frozen).

SPEC SHAPE: `method resolveMediaType ... ensures out = resolvedMediaType guessed encoding` — a TOTAL (loom.semantics.termination total) functional equality with NO precondition. Verify => impl computes resolvedMediaType on the ENTIRE domain. This is the tightest possible spec shape; the discriminating changed op (the 5-key compression table incl. the NEW br+compress keys) is modeled DEEPLY/CONCRETELY in the FROZEN pure region, not behind an axiom. There are NO A-legs and NO deep-model references to attack (meta.json axioms=[], deep_model_references=[]).

VERIFY COMMAND (each): `bash scripts/lean_verify.sh <file>` run from project root, concurrently in batches of 4.
### Results
- pos_control.lean (gold impl): EXIT 0 = VERIFIES.
- atk_1.lean (prepatch bug: 3-key table omitting br+compress; partial-domain): EXIT 1, genuine `unsolved goals` on the br/compress cases. PREPATCH REPRODUCED.
- atk_2.lean (ignore compression, guessed then default; partial-domain): EXIT 1, unsolved goals.
- atk_3.lean (value-swap: br -> application/x-bzip; boundary/value corruption): EXIT 1, unsolved goals.
- atk_4.lean (wrong precedence: guessed.orElse compression; control-flow-effect): EXIT 1, unsolved goals.
- atk_5.lean (ungrounded-oracle ECHO: `return resolvedMediaType guessed encoding`): initially EXIT 3-style artifact `No goals to be solved` at the redundant `simp` line — a PROOF-SCRIPT artifact, not semantic. Removed the redundant `simp [resolvedMediaType]` line (proof body is in the mutable region, still same_spec True) -> EXIT 0 = VERIFIES.
- atk_6.lean (constant application/octet-stream): EXIT 1, unsolved goals.
- atk_7.lean (omit only NEW br key, keep compress; partial boundary): EXIT 1, unsolved goals.
- atk_8.lean (wrong fallback default text/plain): EXIT 1, unsolved goals.

KEY DISTINCTION: all 7 wrong impls fail with GENUINE `unsolved goals` (real semantic mismatch — no proof-strengthening can rescue them because the total equality is literally false for them). atk_5 failed only with `No goals to be solved` (redundant tactic), which a real adversary trivially fixes; once fixed it verifies. This is the ONLY verifying impl besides gold, and it is semantically identical to the reference.

RESOLVE RUN (mandatory for every verifying impl): atk_5's faithful refined patch is byte-identical to the gold patch (the echo computes resolvedMediaType = full 5-key table incl br+compress). Ran via swebench_unified.harness.run_resolve('django__django-16642', <atk_5.patch>): RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the sole verifying wrong-shaped candidate RESOLVES => it does NOT break the spec (a resolving echo of the gold is not a weakness, per G-EQ / G-PANEL-1 resolve policy).

REFINEMENT.MD AUDIT: legs A1..A6 are all R or I (A3 is I: frozen compressionMediaType 5-key match transliterates the post-patch dict key-for-key; A1/A2 R input-provenance to unchanged mimetypes.guess_type, matching meta.json input_provenance; A4 R+I orElse<->dict.get; A5 R getD<->`x or default`; A6 R result<->header). NO kind-3 legs. NO A-consumed / A-reference legs exist (no axioms, no deep-model refs); G-AX correctly vacuous. Model<->patch correspondence holds: the two ADDED dict keys (br, compress) are present in the frozen compressionMediaType table, and G-CONF (recorded) confirmed the R/I shadow == real patched FileResponse Content-Type over 100017 fuzzed names (seed 16642), 0 disagreements.

CONCLUSION: verify => impl == frozen reference (total equality, no precondition) => faithful patch is behaviorally the gold patch => resolves. No verify-but-not-resolve gap possible. >=5 distinct attack families run (partial-domain x3, boundary/value x2, control-flow-effect, echo, constant), none breaks the spec; positive control verifies; the one verifying candidate's materialized patch was executed through the official harness and RESOLVED. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of resolveMediaType model vs the real FileResponse.set_headers media-type resolution slice (django/http/response.py:606-619, patched).

SPEC INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region (axioms/pure/pre/post/signature/ensures) is byte-identical; only the impl+proof differ, so the modeled function is the sole thing under test.

MODEL: resolvedMediaType g e = (compressionMediaType e).orElse (fun _=>g) |>.getD "application/octet-stream"; compressionMediaType maps exactly {br,bzip2,compress,gzip,xz} -> their dedicated types. Real slice = {5-key dict}.get(encoding, content_type) then content_type or "application/octet-stream". Inputs (guessed,encoding) are the UNCHANGED mimetypes.guess_type(filename) pair (input-provenance, no axiom).

DIFFERENTIAL TEST: transliterated shadow vs real PATCHED FileResponse(...).headers['Content-Type'] over 300,013 file names (all boundary cases: every recognised label with/without guessable wrapped type, empty name, dotfiles, unknown exts + 300k fuzzed). 0 disagreements. 5-key table, guess_type labels, and Option.orElse/getD <-> dict.get/or all match on the reachable input domain.

ONLY THEORETICAL DIVERGENCE HUNTED: Python 'x or d' vs Lean 'getD d' differ iff content_type == "" (Python falls to generic, Lean returns ""). UNREACHABLE: mimetypes.guess_type never emits an empty content_type (no empty value in types_map; returns None, not "", for unknowns). mapping.md §2's 'never \"\"' caveat holds for the actual callee output domain, so no diverging input exists.

NOT VACUOUSLY STRONG: Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (3-key table) FAILS to verify precisely on br/compress (unsolved goals at ensures) — the spec discriminates the change. Total-correctness termination semantics is faithful (straight-line lookup, always returns; F2P reads the returned header). No axioms => no unfaithful assumed contract.

Conclusion: model agrees with the real callee on every reachable input; spec is neither too strong nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle is relaxed_leakage=true with an accepted RELAXED_LEAKAGE.md; per gates/_audit.py + the panel recording convention, G-PANEL-3 defers to the disposition and records NO-LEAKAGE (pass)+note UNLESS a NEW leak beyond the dispositioned facet or a broken disposition is found. I independently re-verified rather than rubber-stamping:

(1) SPEC INTEGRITY: diff of Solution.lean vs Solution_prepatch.lean shows the two files differ ONLY inside impl-start/impl-end (prepatch uses the 3-key table, omitting br/compress). The pure region (compressionMediaType/resolvedMediaType), the method signature, and the `ensures out = resolvedMediaType guessed encoding` are byte-identical between them — spec region is shared/frozen, so G-DIFF exercises the impl, not the spec.

(2) CORE SOUNDNESS RE-CONFIRMED: lean_verify.sh Solution.lean -> EXIT=0 (verifies, proof closes). meta.json gates: G-CONF pass (0/100017 disagreements, seed 16642, transliterated shadow vs real patched FileResponse), G-DIFF pass (prepatch fails on the br/compress cases), G-EQ pass (7 same-spec wrong impls rejected incl wrong-brotli-string atk_6; positive control verifies), total-correctness semantics closes the vacuous-divergence loophole. G-AX vacuous (genuinely axiom-free). Disposition's soundness claims hold.

(3) PS TOKEN SCAN: public problem_statement names only INPUT extensions br/Z, the symptom text/html, FileResponse, Mime Type. Tokens brotli, x-brotli, x-compress, application/x, octet-stream, bzip, and the encoding label 'compress' are ALL absent from the PS. (hints_text excluded per instructions; it is only 'Thanks for the report!'.)

(4) LEAK FACET = DISPOSITIONED: the spec view's compressionMediaType reproduces the two gold-added dict entries verbatim -> some "application/x-brotli" and some "application/x-compress". These exact OUTPUT strings appear only in the gold diff and are pinned by the hidden F2P test_compressed_response; a PS-only solver cannot derive x-brotli vs x-br/brotli. This is exactly the facet documented in RELAXED_LEAKAGE.md. The other three table entries (bzip2/gzip/xz) are pre-patch context lines (public repo state), octet-stream is the unchanged generic fallback, and br/compress are input labels (PS + stdlib mimetypes encodings_map) — none constitutes a NEW leak.

(5) UNAVOIDABILITY RE-DERIVED: faithfulness to the post-gold behavior forces the exact strings — a spec leaving them free would admit an impl (e.g. br->application/brotli) that fails the F2P test (spec-too-weak). Faithful + non-leaking is provably impossible. Disposition is NOT broken (no core gate unsound, no PS-only derivation of the exact strings exists).

No leaking line beyond the dispositioned two-output-string facet found. Verdict NO-LEAKAGE (pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
