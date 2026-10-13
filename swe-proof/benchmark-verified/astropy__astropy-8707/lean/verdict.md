# P2 adversarial audit — astropy__astropy-8707

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,9 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  match image with
+  | CardImage.text cs => return Except.ok (padCard cs)
+  | CardImage.bytes _ => return Except.error CardErr.illTyped
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,7 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  return Except.ok (decodeImage image)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,9 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  match image with
+  | CardImage.text cs => return Except.ok (padCard cs)
+  | CardImage.bytes _ => return Except.ok (padCard [])
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,12 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  let cs := decodeImage image
+  let n := cs.length
+  -- wrong: pad to next multiple of (cardWidth-1)
+  let w := cardWidth - 1
+  let r := n % w
+  return Except.ok (if r = 0 then cs else cs ++ List.replicate (w - r) ' ')
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,9 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  let mut cs := decodeImage image
+  cs := cs.dropLast
+  return Except.ok (padCard cs)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -85,22 +85,12 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  return Except.ok (padCard (decodeImage image))
 -- impl-end
 
 -- proof-start
 theorem correct_cardFromString : ∀ (image : CardImage),
     problem_spec_cardFromString image (implementation_cardFromString image) := by
   intro image
-  cases image with
-  | text cs => rfl
-  | bytes bs => rfl
+  rfl
 -- proof-end
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,15 +85,10 @@
 -- impl-start
 def implementation_cardFromString (image : CardImage) :
     Except CardErr (List Char) := Id.run do
-  let mut img := image
-  -- a raw-byte input is first reinterpreted as text, each byte taken as the
-  -- code point equal to its value, before any further processing
-  if let CardImage.bytes bs := img then
-    img := CardImage.text (bytesAsText bs)
-  let chars := match img with
-    | CardImage.text cs  => cs
-    | CardImage.bytes _  => []
-  return Except.ok (padCard chars)
+  match image with
+  | CardImage.text cs => return Except.ok (padCard cs)
+  | CardImage.bytes bs =>
+      return Except.ok (padCard (bs.map (fun b => Char.ofNat (b.toNat % 128))))
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Construction of a constant-width "card image" from a raw input.

The raw input may be supplied in one of two forms:

* as a sequence of text characters, or
* as a sequence of raw 8-bit bytes.

When the input is a sequence of raw bytes, each byte is interpreted directly as
the code point whose numeric value equals that byte (the one-to-one Latin-1
correspondence between byte values 0..255 and the first 256 code points). Once
the input is in textual form it is padded out with trailing spaces to the next
multiple of the constant card width (80 columns): inputs already a positive
multiple of the width are returned unchanged; shorter or non-aligned inputs are
extended with spaces up to the next multiple.

Stated as an input → output relation `image ↦ card-image-text`. Accepting either
form always succeeds. The implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No UNCHANGED dependency callee needs a contract: the textual reinterpretation
-- of raw bytes and the width-padding are both modeled DEEPLY below (the only
-- observable touched by this behavior is the resulting card-image text), so
-- there is no `axiom <callee>_prop` for the proof to consume.

/-- The constant card width, in columns. -/
def cardWidth : Nat := 80

/-- A raw input to card-image construction: either textual characters or a
sequence of raw 8-bit bytes. -/
inductive CardImage where
  | text  : List Char → CardImage
  | bytes : List UInt8 → CardImage
deriving DecidableEq, Repr

/-- Error outcomes of card-image construction. A textual input always succeeds;
this carrier exists to express that an input which cannot be treated as text has
no card image. -/
inductive CardErr where
  | illTyped
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Reinterpret raw bytes as text: each byte becomes the code point whose value
equals the byte (the Latin-1 correspondence; every byte 0..255 maps to a valid
code point). -/
def bytesAsText (bs : List UInt8) : List Char :=
  bs.map (fun b => Char.ofNat b.toNat)

/-- The textual content of a raw input: text passes through; raw bytes are
reinterpreted one byte ↦ one code point. -/
def decodeImage : CardImage → List Char
  | CardImage.text cs  => cs
  | CardImage.bytes bs => bytesAsText bs

/-- Pad text out with trailing spaces to a multiple of the constant card width.
Text already exactly the card width, or a positive multiple of it, is returned
unchanged; otherwise it is extended with spaces up to the next multiple. -/
def padCard (cs : List Char) : List Char :=
  let n := cs.length
  if n = cardWidth then cs
  else if n > cardWidth then
    let r := n % cardWidth
    if r = 0 then cs else cs ++ List.replicate (cardWidth - r) ' '
  else
    let r := n % cardWidth
    cs ++ List.replicate (cardWidth - r) ' '
-- pure-end

-- post-conditions-start
/-- The card image produced from a raw input: the input's textual content
(text as-is; raw bytes reinterpreted one byte ↦ one code point) padded out to a
multiple of the constant card width. Construction always succeeds. -/
def problem_spec_cardFromString (image : CardImage)
    (result : Except CardErr (List Char)) : Prop :=
  result = Except.ok (padCard (decodeImage image))
-- post-conditions-end

-- impl-start
def implementation_cardFromString (image : CardImage) :
    Except CardErr (List Char) := Id.run do
  let mut img := image
  -- a raw-byte input is first reinterpreted as text, each byte taken as the
  -- code point equal to its value, before any further processing
  if let CardImage.bytes bs := img then
    img := CardImage.text (bytesAsText bs)
  let chars := match img with
    | CardImage.text cs  => cs
    | CardImage.bytes _  => []
  return Except.ok (padCard chars)
-- impl-end

-- proof-start
theorem correct_cardFromString : ∀ (image : CardImage),
    problem_spec_cardFromString image (implementation_cardFromString image) := by
  intro image
  cases image with
  | text cs => rfl
  | bytes bs => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality problem_spec_cardFromString image result := result = Except.ok (padCard (decodeImage image)). Pins the output EXACTLY for both CardImage.text and CardImage.bytes constructors. Any closing impl must reproduce the gold observable on both paths, incl. the bytes path Except.ok (padCard (bytesAsText bs)) = the byte->latin-1->pad behavior the gold patch ADDS.

PROTOCOL: same_spec('lean') = True for ALL 7 attacks + positive control (frozen axioms/pure/pre/post byte-identical; edited impl+proof only).

### ATTACKS (7 distinct wrong-impl classes; verifications run concurrently as bg jobs, <=4 at a time):
  cmd each: bash scripts/lean_verify.sh <path>
  - atk1.lean  prepatch bug (bytes->Except.error illTyped)        -> exit 1 (bytes goal reduces to False). PREPATCH REPRODUCED.
  - atk2.lean  drop padding (return Except.ok (decodeImage image)) -> exit 1.
  - atk3.lean  partial-domain (bytes -> padCard [])                -> exit 1.
  - atk4.lean  boundary off-by-one (pad to multiple of width-1=79) -> exit 1.
  - atk5.lean  control-flow-effect (dropLast before pad)           -> exit 1.
  - atk7.lean  ungrounded-oracle echo (ascii-truncate: byte %128)  -> exit 1.
  - atk6.lean  gold-equivalent echo (Except.ok (padCard (decodeImage image))) -> exit 0.
     atk6_ax.lean (+#print axioms correct_cardFromString): exit 0, 'correct_cardFromString does not depend on any axioms' (clean, no sorryAx).
Every genuinely-wrong impl FAILS to close: the exact-equality goal reduces to False on some input (all six pinned on the bytes case). Only the gold-equivalent atk6 closes.

RESOLVE (protocol step 2) on the ONE verifying impl atk6: its faithful patch is byte-identical to the gold patch.diff (diff shows no difference). Wrapper run_resolve() returned COMPLETED=False 'no report ... harness error or image pull failure' (report-path/contention artifact under concurrent audits, NOT a non-resolve). Ran the official harness DIRECTLY to completion:
  cd .../experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path .../preds.json --run_id sbu-eq-atk6-direct --namespace swebench --instance_image_tag latest --cache_level env ----instance_ids astropy__astropy-8707
  RESULT: Instances completed:1, resolved:1, error:0 (Evaluation ✓=1). report.json: resolved=true, FAIL_TO_PASS test_card_from_bytes success, 11/11 PASS_TO_PASS success. => atk6's faithful patch RESOLVES. (Corroborated by prior gold-sanity-8707-a4 report: resolved=true.) verify => resolves holds; no verify-but-non-resolving impl found.

positive_control atk_pos.lean = Solution.lean verbatim -> exit 0.

REFINEMENT.md AUDIT: no `axiom ` declarations in Solution.lean; axiom_check.py is a skip stub -> NO A-consumed / NO kind-3 legs. All legs R / I / A-reference. A-reference correspondence holds: bytesAsText (b => Char.ofNat b.toNat) == bytes.decode('latin1') (latin-1: byte n -> U+00nn, verified for all 256; UInt8 subset 0..255 all valid code points); padCard mirrors _pad (card.py) branch-for-branch with cardWidth=80==Card.length==CARD_LENGTH. G-CONF (conformance_check.py, seed 20240626, >=1e5 draws + boundary matrix) differential-tests both deep models against the real patched Card.fromstring._image. R/I legs mechanically covered by G-CONF per instructions.

CONCLUSION: the exact-equality spec admits no closing impl that omits the bytes fix; the sole closing impl is gold-observable and its faithful patch resolves. verify=>correct. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Construction of a constant-width "card image" from a raw input.

The raw input may be supplied in one of two forms:

* as a sequence of text characters, or
* as a sequence of raw 8-bit bytes.

When the input is a sequence of raw bytes, each byte is interpreted directly as
the code point whose numeric value equals that byte (the one-to-one Latin-1
correspondence between byte values 0..255 and the first 256 code points). Once
the input is in textual form it is padded out with trailing spaces to the next
multiple of the constant card width (80 columns): inputs already a positive
multiple of the width are returned unchanged; shorter or non-aligned inputs are
extended with spaces up to the next multiple.

Stated as an input → output relation `image ↦ card-image-text`. Accepting either
form always succeeds. The implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No UNCHANGED dependency callee needs a contract: the textual reinterpretation
-- of raw bytes and the width-padding are both modeled DEEPLY below (the only
-- observable touched by this behavior is the resulting card-image text), so
-- there is no `axiom <callee>_prop` for the proof to consume.

/-- The constant card width, in columns. -/
def cardWidth : Nat := 80

/-- A raw input to card-image construction: either textual characters or a
sequence of raw 8-bit bytes. -/
inductive CardImage where
  | text  : List Char → CardImage
  | bytes : List UInt8 → CardImage
deriving DecidableEq, Repr

/-- Error outcomes of card-image construction. A textual input always succeeds;
this carrier exists to express that an input which cannot be treated as text has
no card image. -/
inductive CardErr where
  | illTyped
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Reinterpret raw bytes as text: each byte becomes the code point whose value
equals the byte (the Latin-1 correspondence; every byte 0..255 maps to a valid
code point). -/
def bytesAsText (bs : List UInt8) : List Char :=
  bs.map (fun b => Char.ofNat b.toNat)

/-- The textual content of a raw input: text passes through; raw bytes are
reinterpreted one byte ↦ one code point. -/
def decodeImage : CardImage → List Char
  | CardImage.text cs  => cs
  | CardImage.bytes bs => bytesAsText bs

/-- Pad text out with trailing spaces to a multiple of the constant card width.
Text already exactly the card width, or a positive multiple of it, is returned
unchanged; otherwise it is extended with spaces up to the next multiple. -/
def padCard (cs : List Char) : List Char :=
  let n := cs.length
  if n = cardWidth then cs
  else if n > cardWidth then
    let r := n % cardWidth
    if r = 0 then cs else cs ++ List.replicate (cardWidth - r) ' '
  else
    let r := n % cardWidth
    cs ++ List.replicate (cardWidth - r) ' '
-- pure-end

-- post-conditions-start
/-- The card image produced from a raw input: the input's textual content
(text as-is; raw bytes reinterpreted one byte ↦ one code point) padded out to a
multiple of the constant card width. Construction always succeeds. -/
def problem_spec_cardFromString (image : CardImage)
    (result : Except CardErr (List Char)) : Prop :=
  result = Except.ok (padCard (decodeImage image))
-- post-conditions-end

-- impl-start
def implementation_cardFromString (image : CardImage) :
    Except CardErr (List Char) := Id.run do
  let mut img := image
  -- a raw-byte input is first reinterpreted as text, each byte taken as the
  -- code point equal to its value, before any further processing
  if let CardImage.bytes bs := img then
    img := CardImage.text (bytesAsText bs)
  let chars := match img with
    | CardImage.text cs  => cs
    | CardImage.bytes _  => []
  return Except.ok (padCard chars)
-- impl-end

-- proof-start
theorem correct_cardFromString : ∀ (image : CardImage),
    problem_spec_cardFromString image (implementation_cardFromString image) := by
  intro image
  cases image with
  | text cs => rfl
  | bytes bs => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional equality problem_spec_cardFromString image result := result = Except.ok (padCard (decodeImage image)). Pins the output EXACTLY for both CardImage.text and CardImage.bytes constructors. Any closing impl must reproduce the gold observable on both paths, incl. the bytes path Except.ok (padCard (bytesAsText bs)) = the byte->latin-1->pad behavior the gold patch ADDS.

PROTOCOL: same_spec('lean') = True for ALL 7 attacks + positive control (frozen axioms/pure/pre/post byte-identical; edited impl+proof only).

### ATTACKS (7 distinct wrong-impl classes; verifications run concurrently as bg jobs, <=4 at a time):
  cmd each: bash scripts/lean_verify.sh <path>
  - atk1.lean  prepatch bug (bytes->Except.error illTyped)        -> exit 1 (bytes goal reduces to False). PREPATCH REPRODUCED.
  - atk2.lean  drop padding (return Except.ok (decodeImage image)) -> exit 1.
  - atk3.lean  partial-domain (bytes -> padCard [])                -> exit 1.
  - atk4.lean  boundary off-by-one (pad to multiple of width-1=79) -> exit 1.
  - atk5.lean  control-flow-effect (dropLast before pad)           -> exit 1.
  - atk7.lean  ungrounded-oracle echo (ascii-truncate: byte %128)  -> exit 1.
  - atk6.lean  gold-equivalent echo (Except.ok (padCard (decodeImage image))) -> exit 0.
     atk6_ax.lean (+#print axioms correct_cardFromString): exit 0, 'correct_cardFromString does not depend on any axioms' (clean, no sorryAx).
Every genuinely-wrong impl FAILS to close: the exact-equality goal reduces to False on some input (all six pinned on the bytes case). Only the gold-equivalent atk6 closes.

RESOLVE (protocol step 2) on the ONE verifying impl atk6: its faithful patch is byte-identical to the gold patch.diff (diff shows no difference). Wrapper run_resolve() returned COMPLETED=False 'no report ... harness error or image pull failure' (report-path/contention artifact under concurrent audits, NOT a non-resolve). Ran the official harness DIRECTLY to completion:
  cd .../experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path .../preds.json --run_id sbu-eq-atk6-direct --namespace swebench --instance_image_tag latest --cache_level env ----instance_ids astropy__astropy-8707
  RESULT: Instances completed:1, resolved:1, error:0 (Evaluation ✓=1). report.json: resolved=true, FAIL_TO_PASS test_card_from_bytes success, 11/11 PASS_TO_PASS success. => atk6's faithful patch RESOLVES. (Corroborated by prior gold-sanity-8707-a4 report: resolved=true.) verify => resolves holds; no verify-but-non-resolving impl found.

positive_control atk_pos.lean = Solution.lean verbatim -> exit 0.

REFINEMENT.md AUDIT: no `axiom ` declarations in Solution.lean; axiom_check.py is a skip stub -> NO A-consumed / NO kind-3 legs. All legs R / I / A-reference. A-reference correspondence holds: bytesAsText (b => Char.ofNat b.toNat) == bytes.decode('latin1') (latin-1: byte n -> U+00nn, verified for all 256; UInt8 subset 0..255 all valid code points); padCard mirrors _pad (card.py) branch-for-branch with cardWidth=80==Card.length==CARD_LENGTH. G-CONF (conformance_check.py, seed 20240626, >=1e5 draws + boundary matrix) differential-tests both deep models against the real patched Card.fromstring._image. R/I legs mechanically covered by G-CONF per instructions.

CONCLUSION: the exact-equality spec admits no closing impl that omits the bytes fix; the sole closing impl is gold-observable and its faithful patch resolves. verify=>correct. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of astropy__astropy-8707 lean bundle. Modeled function problem_spec_cardFromString pins result = Except.ok(padCard(decodeImage image)) for both CardImage.text and CardImage.bytes. Verified against real repo at base_commit:

1. padCard vs _pad (card.py:1269-1284): _pad = {len==80 -> unchanged; len>80 & len%80==0 -> unchanged; else input + ' '*(80 - len%80)}. padCard reproduces this identically. Boundary evals in Lean (len 0->80, 79->80, 80->80, 81->160, 160->160, 161->240) all match _pad; empty-string case (len 0, r=0) correctly yields 80 spaces in BOTH (else branch, 80-0). Card.length = CARD_LENGTH = 80 confirmed, so cardWidth:=80 faithful; patch does not touch it.
2. bytesAsText vs bytes.decode('latin1'): byte n -> Char.ofNat n; latin-1 maps byte n to U+00nn (code point == byte value) for all 0..255. Lean confirms Char.ofNat 0xFF = 'ÿ'. Full-range identity holds.
3. Except.ok always: real patched Card.fromstring always succeeds for str/bytes and sets card._image (the only observable, parsed by the F2P test test_card_from_bytes). Spec leaves nothing unconstrained (directive 5). CardErr.illTyped is unreachable in patched/spec behavior and only used to model the prepatch crash in Solution_prepatch.lean.

Mechanical checks: lean_verify exit 0, #print axioms correct_cardFromString -> no axioms (clean, no sorryAx). same_spec True self-consistent and post-vs-prepatch (spec region byte-identical). conformance_check.py shadow (shadow_pad/latin-1 join) matches the deep models; recorded G-CONF pass over boundary matrix + 120k fuzzed draws incl. 0x80..0xFF latin-1 range. No input found where the spec disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures): no diff markers, no reproduced gold-patch line (>=8 chars), no patched file path (card.py/header.py) or dotted module path, no spec-view identifier embedding a patched repo symbol, no gold-narration terms in comments/docstrings. same_spec(Solution, Solution_prepatch) = True (frozen regions byte-identical; prepatch differs only in impl/proof).

Semantic judgment: the public problem_statement explicitly states the gold edit's essence — change Header.fromstring/Card.fromstring to 'accept unicode or bytes string types', and notes the code 'assumes that the data can be ASCII-encoded'. The spec view models the input as text|bytes and pins the observable card-image text as padCard(decodeImage image) for both forms. This is exactly the publicly-stated 'accept bytes' behavior; it does NOT expose the isinstance(image, bytes) guard, the image.decode('latin1') call text, the _pad edit site, the patched file paths, or the header.py card-splitting plumbing (all non-public gold mechanics).

The only detail beyond the bare statement is the latin-1 byte->code-point identity (statement says 'ASCII'). But a total, faithful spec of the card-image observable is forced to characterize the byte->char mapping; latin-1 (byte value == code point, the ASCII superset standard for FITS) is a natural behavioral derivation, not a non-public gold trick, and it hands the solver no mechanical edit localization. Judged against problem_statement only (hints_text empty, correctly not used). No line of the spec view leaks the gold edit beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
