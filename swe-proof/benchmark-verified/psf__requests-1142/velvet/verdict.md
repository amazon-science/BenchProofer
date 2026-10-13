# P2 adversarial audit — psf__requests-1142

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
payload = .absent, carriesBody = false : the frozen postcondition demands out = announcedSize .absent false = none. Every wrong impl that mishandles this (or any) case leaves an unsolved goal. Prepatch (always some 0 on absent) fails with exactly `carriesBody = true` unsolved at the .absent case; atk_4 reproduces that same bug and likewise fails verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,12 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
+    -- inverted no-payload decision
     let out : Option Nat :=
       match payload with
       | .seekable   n => some n
       | .measurable n => some n
-      | .absent       => if carriesBody then some 0 else none
+      | .absent       => if carriesBody then none else some 0
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,13 +62,11 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
+    -- off-by-one on the measured size
     let out : Option Nat :=
       match payload with
       | .seekable   n => some n
-      | .measurable n => some n
+      | .measurable n => some (n + 1)
       | .absent       => if carriesBody then some 0 else none
     return out
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,12 +62,10 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
+    -- seekable payload announces nothing (wrong)
     let out : Option Nat :=
       match payload with
-      | .seekable   n => some n
+      | .seekable   _ => none
       | .measurable n => some n
       | .absent       => if carriesBody then some 0 else none
     return out
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,12 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
+    -- no-payload always announces zero, ignoring carriesBody
     let out : Option Nat :=
       match payload with
       | .seekable   n => some n
       | .measurable n => some n
-      | .absent       => if carriesBody then some 0 else none
+      | .absent       => some 0
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,12 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
+    -- no-payload always announces nothing, ignoring carriesBody
     let out : Option Nat :=
       match payload with
       | .seekable   n => some n
       | .measurable n => some n
-      | .absent       => if carriesBody then some 0 else none
+      | .absent       => none
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,8 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
-    let out : Option Nat :=
-      match payload with
-      | .seekable   n => some n
-      | .measurable n => some n
-      | .absent       => if carriesBody then some 0 else none
+    -- ignores the payload shape entirely; decides only from carriesBody
+    let out : Option Nat := if carriesBody then some 0 else none
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,8 @@
   ensures out = announcedSize payload carriesBody
   do
     -- impl-start
-    -- A seekable or directly-measurable payload announces its exact size; with
-    -- no payload present, announce a zero size only when the method
-    -- conventionally carries an entity body, otherwise announce nothing.
-    let out : Option Nat :=
-      match payload with
-      | .seekable   n => some n
-      | .measurable n => some n
-      | .absent       => if carriesBody then some 0 else none
+    -- constant announcement (ungrounded echo of the zero case)
+    let out : Option Nat := some 0
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real size-announcing routine is a straight-line
   dispatch over the payload shape and always terminates, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: the modeled operation decides the announced payload size from the
-- shape of the payload alone (a seekable/measurable/absent payload) and a single
-- boolean property of the request. It calls no unchanged repository callee whose
-- contract must be assumed, so there is nothing to axiomatize. (G-AX skips.)
-- axioms-end

-- pure-start
/- The three observable shapes a request payload can take, as far as announcing
   its size is concerned:
   * `seekable n` — a payload that can be positioned and queried, so its size
     `n` is read back directly;
   * `measurable n` — an in-memory payload whose size `n` is measured directly;
   * `absent` — no payload is present at all. -/
inductive Payload where
  | seekable   (size : Nat)
  | measurable (size : Nat)
  | absent

/- The announced payload size for a request.

   When a payload is present in either form, its exact size is announced. When
   no payload is present, the announcement depends on whether the request method
   conventionally carries an entity body: a method that does carry one announces
   a zero size, while a method that conventionally carries none announces nothing
   at all (`none` — no size is attached). This is the abstract desired behavior:
   a body-less request whose method conventionally has no entity body must not be
   forced to announce a (zero) size. -/
def announcedSize (p : Payload) (carriesBody : Bool) : Option Nat :=
  match p with
  | .seekable   n => some n
  | .measurable n => some n
  | .absent       => if carriesBody then some 0 else none

@[simp] lemma announcedSize_seekable (n : Nat) (b : Bool) :
    announcedSize (.seekable n) b = some n := rfl
@[simp] lemma announcedSize_measurable (n : Nat) (b : Bool) :
    announcedSize (.measurable n) b = some n := rfl
@[simp] lemma announcedSize_absent (b : Bool) :
    announcedSize .absent b = (if b then some 0 else none) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method contentLength (payload : Payload) (carriesBody : Bool) return (out : Option Nat)
  ensures out = announcedSize payload carriesBody
  do
    -- impl-start
    -- A seekable or directly-measurable payload announces its exact size; with
    -- no payload present, announce a zero size only when the method
    -- conventionally carries an entity body, otherwise announce nothing.
    let out : Option Nat :=
      match payload with
      | .seekable   n => some n
      | .measurable n => some n
      | .absent       => if carriesBody then some 0 else none
    return out
    -- impl-end

prove_correct contentLength by
  loom_solve
  cases payload <;> simp_all [announcedSize]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The frozen postcondition is an EXACT functional equality `out = announcedSize payload carriesBody`, with announcedSize fully spelled out (seekable n->some n; measurable n->some n; absent->if carriesBody then some 0 else none) and NO axioms / NO A-references (meta.json: axioms=[], deep_model_references=[], conf_skip=False). This leaves no semantic slack for a verifying-but-wrong impl.

TOOLING: verifier `bash scripts/lean_verify.sh <f>`; same_spec via swebench-lean venv get_backend('velvet'). All 10 files (7 attacks + correct_alt + positive_control + prepatch) return same_spec=True (impl region only edited; axioms/pure/pre/post byte-identical).

BASELINE: positive_control.lean EXIT=0 (verifies). prepatch.lean EXIT=1 unsolved goal `carriesBody = true` at case .absent -> PREPATCH BUG REPRODUCED (F2P body-less GET/HEAD scenario). correct_alt.lean (nested-if spelling of same semantics) EXIT=0 -> verify path admits variants, not vacuously rejecting.

7 DISTINCT SAME-SPEC WRONG IMPLS, all run via lean_verify.sh (batches of 4, concurrent), ALL FAIL verify with genuine `error: unsolved goals` (NOT syntax errors):
  atk_1 EXIT=1  inverted no-payload decision (absent -> if carriesBody then none else some 0) [control-flow-effect]
  atk_2 EXIT=1  off-by-one on measured size (measurable n -> some (n+1)) [arithmetic/boundary]
  atk_3 EXIT=1  seekable payload announces nothing (seekable _ -> none) [partial-domain/boundary]
  atk_4 EXIT=1  no-payload always some 0 ignoring carriesBody == the PREPATCH BUG shape [prepatch bug re-encoded]
  atk_5 EXIT=1  no-payload always none, drops the body-carrying zero [partial-domain]
  atk_6 EXIT=1  ignores payload shape entirely, decides only from carriesBody [control-flow degeneracy]
  atk_7 EXIT=1  constant some 0 (ungrounded-oracle echo of the zero case) [ungrounded echo]
Error locations: atk_1..5 at line 74 (match), atk_6/7 at line 70 (const) — all `unsolved goals` on the ensures goal.

PROTOCOL STEP 2 (materialize+resolve faithful patch for each VERIFYING wrong impl): VACUOUS — zero wrong impls verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. No run_resolve was NEEDED (resolve is only required to break the spec via a verifying wrong impl); none exists. verify => correct holds for the exhibited attack surface.

REFINEMENT.MD AUDIT (A-legs): meta.json confirms axioms=[] and deep_model_references=[] => there are NO A-consumed and NO A-reference legs to attack; the R/I legs (A1-A6) are G-CONF's burden (out of G-EQ A-leg scope, mechanically covered by G-CONF/G-CONF conformance_check.py present). refinement.md §C correctly asserts no kind-3 step; every leg is tagged R or I, consistent with the byte-empty axioms region in the frozen Solution.lean. Model<->patch correspondence verified by tracing the gold hunk: seek+tell->str(tell())=some n; elif body is not None->str(len)=some n; elif method not in (GET,HEAD)->'0'=some 0 (carriesBody); else no write=none. This is exactly announcedSize's 4-way behavior; conformance_check.py transliterates it faithfully with pinned seed 1142.

VERDICT: SOUND — >=5 (7) distinct same-spec wrong impls verified-checked, none verifies (so none can break the spec), prepatch reproduced, positive control + a semantic variant both verify. verify => correct is upheld for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
payload = .absent, carriesBody = false : the frozen postcondition demands out = announcedSize .absent false = none. Every wrong impl that mishandles this (or any) case leaves an unsolved goal. Prepatch (always some 0 on absent) fails with exactly `carriesBody = true` unsolved at the .absent case; atk_4 reproduces that same bug and likewise fails verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real size-announcing routine is a straight-line
   dispatch over the payload shape and always terminates, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms: the modeled operation decides the announced payload size from the
-- shape of the payload alone (a seekable/measurable/absent payload) and a single
-- boolean property of the request. It calls no unchanged repository callee whose
-- contract must be assumed, so there is nothing to axiomatize. (G-AX skips.)
-- axioms-end

-- pure-start
/- The three observable shapes a request payload can take, as far as announcing
   its size is concerned:
   * `seekable n` — a payload that can be positioned and queried, so its size
     `n` is read back directly;
   * `measurable n` — an in-memory payload whose size `n` is measured directly;
   * `absent` — no payload is present at all. -/
inductive Payload where
  | seekable   (size : Nat)
  | measurable (size : Nat)
  | absent

/- The announced payload size for a request.

   When a payload is present in either form, its exact size is announced. When
   no payload is present, the announcement depends on whether the request method
   conventionally carries an entity body: a method that does carry one announces
   a zero size, while a method that conventionally carries none announces nothing
   at all (`none` — no size is attached). This is the abstract desired behavior:
   a body-less request whose method conventionally has no entity body must not be
   forced to announce a (zero) size. -/
def announcedSize (p : Payload) (carriesBody : Bool) : Option Nat :=
  match p with
  | .seekable   n => some n
  | .measurable n => some n
  | .absent       => if carriesBody then some 0 else none

@[simp] lemma announcedSize_seekable (n : Nat) (b : Bool) :
    announcedSize (.seekable n) b = some n := rfl
@[simp] lemma announcedSize_measurable (n : Nat) (b : Bool) :
    announcedSize (.measurable n) b = some n := rfl
@[simp] lemma announcedSize_absent (b : Bool) :
    announcedSize .absent b = (if b then some 0 else none) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method contentLength (payload : Payload) (carriesBody : Bool) return (out : Option Nat)
  ensures out = announcedSize payload carriesBody
  do
    -- impl-start
    -- A seekable or directly-measurable payload announces its exact size; with
    -- no payload present, announce a zero size only when the method
    -- conventionally carries an entity body, otherwise announce nothing.
    let out : Option Nat :=
      match payload with
      | .seekable   n => some n
      | .measurable n => some n
      | .absent       => if carriesBody then some 0 else none
    return out
    -- impl-end

prove_correct contentLength by
  loom_solve
  cases payload <;> simp_all [announcedSize]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The frozen postcondition is an EXACT functional equality `out = announcedSize payload carriesBody`, with announcedSize fully spelled out (seekable n->some n; measurable n->some n; absent->if carriesBody then some 0 else none) and NO axioms / NO A-references (meta.json: axioms=[], deep_model_references=[], conf_skip=False). This leaves no semantic slack for a verifying-but-wrong impl.

TOOLING: verifier `bash scripts/lean_verify.sh <f>`; same_spec via swebench-lean venv get_backend('velvet'). All 10 files (7 attacks + correct_alt + positive_control + prepatch) return same_spec=True (impl region only edited; axioms/pure/pre/post byte-identical).

BASELINE: positive_control.lean EXIT=0 (verifies). prepatch.lean EXIT=1 unsolved goal `carriesBody = true` at case .absent -> PREPATCH BUG REPRODUCED (F2P body-less GET/HEAD scenario). correct_alt.lean (nested-if spelling of same semantics) EXIT=0 -> verify path admits variants, not vacuously rejecting.

7 DISTINCT SAME-SPEC WRONG IMPLS, all run via lean_verify.sh (batches of 4, concurrent), ALL FAIL verify with genuine `error: unsolved goals` (NOT syntax errors):
  atk_1 EXIT=1  inverted no-payload decision (absent -> if carriesBody then none else some 0) [control-flow-effect]
  atk_2 EXIT=1  off-by-one on measured size (measurable n -> some (n+1)) [arithmetic/boundary]
  atk_3 EXIT=1  seekable payload announces nothing (seekable _ -> none) [partial-domain/boundary]
  atk_4 EXIT=1  no-payload always some 0 ignoring carriesBody == the PREPATCH BUG shape [prepatch bug re-encoded]
  atk_5 EXIT=1  no-payload always none, drops the body-carrying zero [partial-domain]
  atk_6 EXIT=1  ignores payload shape entirely, decides only from carriesBody [control-flow degeneracy]
  atk_7 EXIT=1  constant some 0 (ungrounded-oracle echo of the zero case) [ungrounded echo]
Error locations: atk_1..5 at line 74 (match), atk_6/7 at line 70 (const) — all `unsolved goals` on the ensures goal.

PROTOCOL STEP 2 (materialize+resolve faithful patch for each VERIFYING wrong impl): VACUOUS — zero wrong impls verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. No run_resolve was NEEDED (resolve is only required to break the spec via a verifying wrong impl); none exists. verify => correct holds for the exhibited attack surface.

REFINEMENT.MD AUDIT (A-legs): meta.json confirms axioms=[] and deep_model_references=[] => there are NO A-consumed and NO A-reference legs to attack; the R/I legs (A1-A6) are G-CONF's burden (out of G-EQ A-leg scope, mechanically covered by G-CONF/G-CONF conformance_check.py present). refinement.md §C correctly asserts no kind-3 step; every leg is tagged R or I, consistent with the byte-empty axioms region in the frozen Solution.lean. Model<->patch correspondence verified by tracing the gold hunk: seek+tell->str(tell())=some n; elif body is not None->str(len)=some n; elif method not in (GET,HEAD)->'0'=some 0 (carriesBody); else no write=none. This is exactly announcedSize's 4-way behavior; conformance_check.py transliterates it faithfully with pinned seed 1142.

VERDICT: SOUND — >=5 (7) distinct same-spec wrong impls verified-checked, none verifies (so none can break the spec), prepatch reproduced, positive control + a semantic variant both verify. verify => correct is upheld for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for psf__requests-1142 velvet. Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec with LeanBackend = True). Solution.lean elaborates clean (lean_verify exit 0); prepatch fails precisely at the `absent`/`carriesBody=false` goal (`⊢ carriesBody = true` unsolved), confirming the spec pins the changed decision and is neither too weak nor too strong.

Modeled function `announcedSize (p : Payload) (carriesBody : Bool) : Option Nat` vs the real gold callee `prepare_content_length` (requests/models.py:388, verified at base_commit 22623bd8 plus the gold hunk). Exhaustive branch comparison over the full modeled domain:
  - seekable n  -> gold sets Content-Length=str(body.tell())=n ; model `some n`  (matches; note the seek/tell branch fires before the method test in real code, so it announces regardless of method — model correctly ignores carriesBody here).
  - measurable n -> gold sets Content-Length=str(len(body))=n ; model `some n`.
  - absent & carriesBody -> gold `elif method not in (GET,HEAD): Content-Length='0'` ; model `some 0`.
  - absent & !carriesBody -> gold writes no header (leading unconditional '0' removed) ; model `none` (header absent — and Content-Length is the only header this method writes, so absence is observable).

Mapping fidelity confirmed: carriesBody <-> method not in ('GET','HEAD') is sound because prepare_method upper-cases self.method (models.py:272) before prepare_content_length runs, so the membership test is over normalized tokens. No axioms / no reference callees — every op is R/I, correctly modeled deeply. No input in the modeled domain diverges from the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True); impl and proof are elided in the consumer spec view. The spec encodes the desired behavior abstractly: postcondition `ensures out = announcedSize payload carriesBody` with the discriminating case `announcedSize .absent (carriesBody) = if carriesBody then some 0 else none`. This does NOT leak the gold edit beyond the public problem_statement. The PS itself already states the desired behavior explicitly ('requests.get is ALWAYS sending content length... the right behavior is not to add this header automatically in GET requests'). Crucially, the spec view: (1) contains NO concrete method tokens ('GET'/'HEAD') — the discriminator is abstracted as the boolean `carriesBody`, with the concrete binding `carriesBody ⟺ method ∉ {GET,HEAD}` living only in mapping.md §2.1 (audit-side, not consumer view); (2) contains NO 'Content-Length' string or header/seek/tell machinery specifics; (3) uses only abstract prose ('a method that conventionally carries none announces nothing at all'), which matches the PS subject rather than gold-patch phrasing. The HEAD half of the discriminator (which the PS never mentions, only GET) is not revealed — abstracted away by carriesBody. G-LEAK lexical screen recorded pass with clean spec view. A spec necessarily encodes desired behavior; here nothing beyond the public issue is disclosed and no gold-reconstruction shortcut is provided.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
