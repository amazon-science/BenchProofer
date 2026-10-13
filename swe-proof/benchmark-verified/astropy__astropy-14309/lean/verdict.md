# P2 adversarial audit — astropy__astropy-14309

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec impl has a faithful patch that fails to resolve. The only attack that closes (atk_7) is an extensional echo of gold whose faithful patch IS the gold patch, which RESOLVES (FAIL_TO_PASS test_is_fits_gh_14305 passes; all PASS_TO_PASS pass).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,8 @@
   if let some content := fileobj then
     return Except.ok (content.take 30 == fitsSignature)
   if let some p := filepath then
-    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
+    if endsWithAny (p.map Char.toLower) fitsExtensions then
+      return Except.ok true
   match args with
   | [] => return Except.error ()
   | a :: _ => return Except.ok a
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
 def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
     Except Unit Bool := Id.run do
   if let some content := fileobj then
-    return Except.ok (content.take 30 == fitsSignature)
+    return Except.ok (content.take 29 == fitsSignature)
   if let some p := filepath then
     return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
   match args with
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,10 @@
 -- impl-start
 def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
     Except Unit Bool := Id.run do
+  if let some p := filepath then
+    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
   if let some content := fileobj then
     return Except.ok (content.take 30 == fitsSignature)
-  if let some p := filepath then
-    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
   match args with
   | [] => return Except.error ()
   | a :: _ => return Except.ok a
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
   if let some p := filepath then
     return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
   match args with
-  | [] => return Except.error ()
+  | [] => return Except.ok false
   | a :: _ => return Except.ok a
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
   if let some content := fileobj then
     return Except.ok (content.take 30 == fitsSignature)
   if let some p := filepath then
-    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
+    return Except.ok (endsWithAny p fitsExtensions)
   match args with
   | [] => return Except.error ()
   | a :: _ => return Except.ok a
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
     return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
   match args with
   | [] => return Except.error ()
-  | a :: _ => return Except.ok a
+  | a :: _ => return Except.ok (!a)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,14 +56,16 @@
 
 -- impl-start
 def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
-    Except Unit Bool := Id.run do
-  if let some content := fileobj then
-    return Except.ok (content.take 30 == fitsSignature)
-  if let some p := filepath then
-    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
-  match args with
-  | [] => return Except.error ()
-  | a :: _ => return Except.ok a
+    Except Unit Bool :=
+  match fileobj with
+  | some content => Except.ok (content.take 30 == fitsSignature)
+  | none =>
+    match filepath with
+    | some p => Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
+    | none =>
+      match args with
+      | [] => Except.error ()
+      | a :: _ => Except.ok a
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Every operation the
-- modeled routine performs — the leading 30-byte signature compare, the
-- case-insensitive filename-suffix test, and the membership probe on the first
-- positional argument — is modeled DEEPLY below (the suffix test is validated as
-- an A-reference against the real standard-library string operations by G-AX).
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The constant leading byte sequence that marks a FITS stream (its first 30
bytes). Compared against the leading bytes read from a file-like input. -/
def fitsSignature : List Char := "SIMPLE  =                    T".toList

/-- The recognised case-insensitive filename suffixes for a FITS path. -/
def fitsExtensions : List (List Char) :=
  [ ".fits".toList, ".fits.gz".toList, ".fit".toList,
    ".fit.gz".toList, ".fts".toList, ".fts.gz".toList ]

/-- `True` iff `s` ends with at least one of the given suffixes. -/
def endsWithAny (s : List Char) (suffixes : List (List Char)) : Bool :=
  suffixes.any (fun suf => suf.isSuffixOf s)
-- pure-end

-- post-conditions-start
/-- Whether the inputs denote a FITS source, as an `Except` whose `error`
captures the out-of-range access that occurs when no positional argument is
available to probe.

Priority of evidence, highest first:
* a readable input is present (`fileobj`): the result is the boolean comparison
  of its leading 30 bytes against the FITS signature;
* otherwise a path is present (`filepath`): the result is the boolean test of
  whether the lower-cased path ends with a recognised FITS suffix — and this is
  the full answer for a path, whether or not a suffix matches;
* otherwise the answer is the membership flag of the first positional argument,
  and if there is no such argument the access is out of range (`error`).

Every output component is pinned to the inputs (frame discipline): the result is
fully determined by `fileobj`, then `filepath`, then `args`. -/
def problem_spec_isFits (filepath fileobj : Option (List Char)) (args : List Bool)
    (result : Except Unit Bool) : Prop :=
  match fileobj with
  | some content => result = Except.ok (content.take 30 == fitsSignature)
  | none =>
    match filepath with
    | some p => result = Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
    | none =>
      match args with
      | [] => result = Except.error ()
      | a :: _ => result = Except.ok a
-- post-conditions-end

-- impl-start
def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
    Except Unit Bool := Id.run do
  if let some content := fileobj then
    return Except.ok (content.take 30 == fitsSignature)
  if let some p := filepath then
    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
  match args with
  | [] => return Except.error ()
  | a :: _ => return Except.ok a
-- impl-end

-- proof-start
theorem correct_isFits : ∀ (filepath fileobj : Option (List Char)) (args : List Bool),
    problem_spec_isFits filepath fileobj args
      (implementation_isFits filepath fileobj args) := by
  intro filepath fileobj args
  unfold problem_spec_isFits implementation_isFits
  cases fileobj with
  | some content => rfl
  | none =>
    cases filepath with
    | some p => rfl
    | none =>
      cases args with
      | nil => rfl
      | cons a as => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total exact-equality spec. problem_spec_isFits pins `result` UNIQUELY in every branch (fileobj => ok(take30==fitsSignature); filepath => ok(endsWithAny (map toLower) exts); args [] => error(); a::_ => ok(a)). meta.json: axioms=[], opaque_callees=[]. The sole A-leg is deep_model_reference row 4 (endsWithAny/fitsExtensions), G-AX-validated == filepath.lower().endswith(...). Any verifying same-spec impl must therefore be pointwise-equal to gold across the whole modeled domain.

same_spec: True for all 7 attacks (axioms/pure/pre/post byte-identical; edited impl+proof regions only). Confirmed via swebench_unified.markers.same_spec with lean backend.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- pos_control (gold impl): EXIT 0; `#print axioms correct_isFits` => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (path only short-circuits on suffix MATCH, else falls through to args): EXIT 1 (cannot close). Witness: filepath=some non-fits, fileobj=none, args=[] => impl=error(), spec=ok(false). = prepatch_reproduced, genuine G-DIFF signal.
- atk_2 boundary (take 29 vs take 30): EXIT 1. Witness: fileobj whose 30th byte affects equality.
- atk_3 control-flow (filepath branch checked BEFORE fileobj): EXIT 1. Witness: both present, non-fits path.
- atk_4 partial-domain (args=[] => ok(false) instead of error()): EXIT 1. Witness: all-none, args=[].
- atk_5 ungrounded/dropped-op (drop map Char.toLower => case-sensitive suffix): EXIT 1. Witness: 'X.FITS' => impl=ok(false), spec=ok(true).
- atk_6 control-flow-effect (negate args head => ok(!a)): EXIT 1. Witness: args=[true].
- atk_7 echo (nested match, no Id.run, extensionally identical to gold): EXIT 0; clean axioms ('does not depend on any axioms').

RESOLVE (protocol step 2 — every verifying impl's faithful patch run through run_resolve): only atk_7 closes. atk_7 is behaviorally identical to gold on the entire modeled domain, so its faithful refined patch IS the gold post-patch is_fits. run_resolve('astropy__astropy-14309', atk_7.patch) => RESOLVED=True, completed=True, note='resolved'; FAIL_TO_PASS test_is_fits_gh_14305 success, all PASS_TO_PASS success. A resolving echo of gold is NOT a weakness (project policy). No verifying impl has a non-resolving faithful patch => verify does NOT outrun correct here.

REFINEMENT.MD AUDIT: 6 legs. Row1 (fileobj None/value) = R; Row2 (take30==sig) = I; Row3 (filepath None/value) = R; Row4 (endsWithAny suffix test) = A-reference (deep model, G-AX validated == str.lower().endswith); Row5 (args[] => error) = I; Row6 (head flag) = I. No A-consumed, no kind-3 (changed-inexpressible). A-reference correspondence holds: suffixes are pure ASCII so Char.toLower per-code-point mirrors str.lower for the decision carrier; axiom_check.py fuzzes 50k+ inputs, 0 mismatches. No UNCHANGED callee consumed as an axiom (axioms region empty; FITS_SIGNATURE inlined as data).

CONCLUSION: >=6 distinct wrong impls attempted; all fail to close. The one closing impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. Spec is a total exact-equality oracle — maximally strong; no verify⇏correct gap found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec impl has a faithful patch that fails to resolve. The only attack that closes (atk_7) is an extensional echo of gold whose faithful patch IS the gold patch, which RESOLVES (FAIL_TO_PASS test_is_fits_gh_14305 passes; all PASS_TO_PASS pass).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Every operation the
-- modeled routine performs — the leading 30-byte signature compare, the
-- case-insensitive filename-suffix test, and the membership probe on the first
-- positional argument — is modeled DEEPLY below (the suffix test is validated as
-- an A-reference against the real standard-library string operations by G-AX).
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The constant leading byte sequence that marks a FITS stream (its first 30
bytes). Compared against the leading bytes read from a file-like input. -/
def fitsSignature : List Char := "SIMPLE  =                    T".toList

/-- The recognised case-insensitive filename suffixes for a FITS path. -/
def fitsExtensions : List (List Char) :=
  [ ".fits".toList, ".fits.gz".toList, ".fit".toList,
    ".fit.gz".toList, ".fts".toList, ".fts.gz".toList ]

/-- `True` iff `s` ends with at least one of the given suffixes. -/
def endsWithAny (s : List Char) (suffixes : List (List Char)) : Bool :=
  suffixes.any (fun suf => suf.isSuffixOf s)
-- pure-end

-- post-conditions-start
/-- Whether the inputs denote a FITS source, as an `Except` whose `error`
captures the out-of-range access that occurs when no positional argument is
available to probe.

Priority of evidence, highest first:
* a readable input is present (`fileobj`): the result is the boolean comparison
  of its leading 30 bytes against the FITS signature;
* otherwise a path is present (`filepath`): the result is the boolean test of
  whether the lower-cased path ends with a recognised FITS suffix — and this is
  the full answer for a path, whether or not a suffix matches;
* otherwise the answer is the membership flag of the first positional argument,
  and if there is no such argument the access is out of range (`error`).

Every output component is pinned to the inputs (frame discipline): the result is
fully determined by `fileobj`, then `filepath`, then `args`. -/
def problem_spec_isFits (filepath fileobj : Option (List Char)) (args : List Bool)
    (result : Except Unit Bool) : Prop :=
  match fileobj with
  | some content => result = Except.ok (content.take 30 == fitsSignature)
  | none =>
    match filepath with
    | some p => result = Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
    | none =>
      match args with
      | [] => result = Except.error ()
      | a :: _ => result = Except.ok a
-- post-conditions-end

-- impl-start
def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :
    Except Unit Bool := Id.run do
  if let some content := fileobj then
    return Except.ok (content.take 30 == fitsSignature)
  if let some p := filepath then
    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)
  match args with
  | [] => return Except.error ()
  | a :: _ => return Except.ok a
-- impl-end

-- proof-start
theorem correct_isFits : ∀ (filepath fileobj : Option (List Char)) (args : List Bool),
    problem_spec_isFits filepath fileobj args
      (implementation_isFits filepath fileobj args) := by
  intro filepath fileobj args
  unfold problem_spec_isFits implementation_isFits
  cases fileobj with
  | some content => rfl
  | none =>
    cases filepath with
    | some p => rfl
    | none =>
      cases args with
      | nil => rfl
      | cons a as => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total exact-equality spec. problem_spec_isFits pins `result` UNIQUELY in every branch (fileobj => ok(take30==fitsSignature); filepath => ok(endsWithAny (map toLower) exts); args [] => error(); a::_ => ok(a)). meta.json: axioms=[], opaque_callees=[]. The sole A-leg is deep_model_reference row 4 (endsWithAny/fitsExtensions), G-AX-validated == filepath.lower().endswith(...). Any verifying same-spec impl must therefore be pointwise-equal to gold across the whole modeled domain.

same_spec: True for all 7 attacks (axioms/pure/pre/post byte-identical; edited impl+proof regions only). Confirmed via swebench_unified.markers.same_spec with lean backend.

### VERIFY RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- pos_control (gold impl): EXIT 0; `#print axioms correct_isFits` => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (path only short-circuits on suffix MATCH, else falls through to args): EXIT 1 (cannot close). Witness: filepath=some non-fits, fileobj=none, args=[] => impl=error(), spec=ok(false). = prepatch_reproduced, genuine G-DIFF signal.
- atk_2 boundary (take 29 vs take 30): EXIT 1. Witness: fileobj whose 30th byte affects equality.
- atk_3 control-flow (filepath branch checked BEFORE fileobj): EXIT 1. Witness: both present, non-fits path.
- atk_4 partial-domain (args=[] => ok(false) instead of error()): EXIT 1. Witness: all-none, args=[].
- atk_5 ungrounded/dropped-op (drop map Char.toLower => case-sensitive suffix): EXIT 1. Witness: 'X.FITS' => impl=ok(false), spec=ok(true).
- atk_6 control-flow-effect (negate args head => ok(!a)): EXIT 1. Witness: args=[true].
- atk_7 echo (nested match, no Id.run, extensionally identical to gold): EXIT 0; clean axioms ('does not depend on any axioms').

RESOLVE (protocol step 2 — every verifying impl's faithful patch run through run_resolve): only atk_7 closes. atk_7 is behaviorally identical to gold on the entire modeled domain, so its faithful refined patch IS the gold post-patch is_fits. run_resolve('astropy__astropy-14309', atk_7.patch) => RESOLVED=True, completed=True, note='resolved'; FAIL_TO_PASS test_is_fits_gh_14305 success, all PASS_TO_PASS success. A resolving echo of gold is NOT a weakness (project policy). No verifying impl has a non-resolving faithful patch => verify does NOT outrun correct here.

REFINEMENT.MD AUDIT: 6 legs. Row1 (fileobj None/value) = R; Row2 (take30==sig) = I; Row3 (filepath None/value) = R; Row4 (endsWithAny suffix test) = A-reference (deep model, G-AX validated == str.lower().endswith); Row5 (args[] => error) = I; Row6 (head flag) = I. No A-consumed, no kind-3 (changed-inexpressible). A-reference correspondence holds: suffixes are pure ASCII so Char.toLower per-code-point mirrors str.lower for the decision carrier; axiom_check.py fuzzes 50k+ inputs, 0 mismatches. No UNCHANGED callee consumed as an axiom (axioms region empty; FITS_SIGNATURE inlined as data).

CONCLUSION: >=6 distinct wrong impls attempted; all fail to close. The one closing impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. Spec is a total exact-equality oracle — maximally strong; no verify⇏correct gap found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack on the frozen problem_spec_isFits vs real post-patch astropy.io.fits.connect.is_fits (patch.diff verified: elif filepath branch now `return filepath.lower().endswith((...))`).

### Verification done
- Solution.lean compiles via lean_verify.sh (exit 0, no sorry); `#print axioms correct_isFits` => 'does not depend on any axioms' (proof genuine, not sorryAx). axioms region empty, opaque_callees empty.
- Spec region byte-identical: same_spec(Solution, Solution_prepatch, lean-backend)=True, so the frozen spec is truly frozen across the patch (the impl/proof differ, spec doesn't). G-PANEL-3 concern N/A.
- Real repo confirmed: FITS_SIGNATURE = b"SIMPLE  =                    T" (30 bytes); Lean fitsSignature is byte-identical (30 chars, codepoints match). Extensions tuple matches source order.

Branch-by-branch faithfulness:
1. fileobj present: spec = ok(content.take 30 == fitsSignature) <-> Python reads read(30), compares to 30-byte sig. take 30 faithfully models read(30) truncation. FAITHFUL.
2. filepath present (the CHANGED branch): spec = ok(endsWithAny (p.map Char.toLower) fitsExtensions) <-> `filepath.lower().endswith(EXTS)` returned as FULL answer. This is exactly the fix (present non-matching path -> ok(false), not fall-through to args). FAITHFUL.
3. neither, args=[] : spec = error() <-> args[0] IndexError (the issue's bug site, still raised post-patch). FAITHFUL.
4. neither, a::_ : spec = ok(a) <-> isinstance(args[0],(...)) membership flag; args modeled as List Bool of pre-reduced flags, tail unobserved as in Python. FAITHFUL.

HARDEST ATTACK (str.lower faithfulness): Lean Char.toLower is ASCII-only (verified: 'A'->'a', but 'İ'/U+0130 and Kelvin U+212A left unchanged), whereas Python str.lower() is full-Unicode and can change length. Brute-forced all codepoints 0x80..0x10FFFF: the ONLY non-ASCII char whose Python lower() yields suffix-relevant ASCII is İ (U+0130) -> 'i' + combining dot (len 2). Probed whether this can create/destroy an endswith match against the six ASCII suffixes: it cannot (the combining dot and the leading 'i' never form a suffix ending in .fits/.fit/.fts/... variants). Explicit probes (İ.fits, x.fitİ, .fİts, café.FITS, etc.) all agree py==lean. So the ASCII-only vs Unicode-lower difference is unobservable through endsWithAny on these suffixes.

conformance_check.py (real callee p.lower().endswith(EXTS)) run: 120012 inputs, 0 disagreements (seed 14309). G-CONF/G-AX/G-EQ/G-PANEL-1/2/3 all recorded pass.

No diverging input found. The modeled function agrees with the real post-patch is_fits on all reachable inputs under the stated (well-justified, frame-disciplined) type bijection. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); leakage.screen over the lean spec view returns passed=True, hard_failures=[] (no diff markers, no reproduced gold-patch line, no patched file path, no patched-symbol identifier/comment collision, no bug/fix narration).

Semantic judgment (the part the lexical screen can miss): the gold edit makes the filepath branch return `filepath.lower().endswith((.fits,.fits.gz,.fit,.fit.gz,.fts,.fts.gz))` directly as the full answer instead of only short-circuiting on a match and falling through to `isinstance(args[0], ...)`, which raises IndexError on empty args. Every element of that edit is ALREADY public in problem_statement (NOT hints_text): the traceback quotes the exact six-suffix tuple (lines 68-70), the failing `return isinstance(args[0], ...)` line (72), the `IndexError: tuple index out of range`, and @saimn's verbatim root cause: 'When filepath is a string without a FITS extension, the function was returning None, now it executes isinstance(args[0], ...)'.

The spec view (fitsSignature, fitsExtensions, endsWithAny, problem_spec_isFits pinning filepath->suffix-boolean-as-full-answer and args=[]->error) describes the correct total behavior — legitimate spec content — and discloses nothing about the edit beyond that public diagnosis. The only branch detailed but not in the problem_statement (fileobj read(30)/signature compare) is UNCHANGED surrounding behavior, so it cannot leak the gold edit. hints_text ('cc @nstarman from #14274') contributes nothing to the spec view.

Conclusion: no line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).