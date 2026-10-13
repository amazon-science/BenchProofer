# P2 adversarial audit — django__django-13279

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,10 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
+    -- WRONG(swapped): emit standard in legacy mode and legacy otherwise.
     let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
-      else standardEncoding sessionData
+      if legacyHashMode then standardEncoding sessionData
+      else legacyEncoding sessionData
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,8 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
-    let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
-      else standardEncoding sessionData
+    -- WRONG(always-legacy): ignore mode, always emit legacy form.
+    let result : Encoded := legacyEncoding sessionData
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,8 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
-    let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
-      else standardEncoding sessionData
+    -- WRONG(prepatch): ignore mode, always emit standard form.
+    let result : Encoded := standardEncoding sessionData
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,10 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
+    -- WRONG(partial): legacy branch correct, standard branch emits legacy form.
     let result : Encoded :=
       if legacyHashMode then legacyEncoding sessionData
-      else standardEncoding sessionData
+      else legacyEncoding sessionData
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,8 +81,9 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
+    -- WRONG(negated): dispatch on the negation of the mode flag.
     let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
+      if !legacyHashMode then legacyEncoding sessionData
       else standardEncoding sessionData
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,11 +81,12 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
-    let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
-      else standardEncoding sessionData
-    return result
+    -- ECHO(correct, different syntax): match on the flag; legacy branch expands
+    -- the composition inline; standard branch returns the standard form.
+    match legacyHashMode with
+    | true  => return wrap (hashOf (serialize sessionData)) (serialize sessionData)
+    | false => return standardEncoding sessionData
     -- impl-end
 
 prove_correct encodeSession by
-  loom_solve
+  loom_solve <;> simp_all [legacyEncoding]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,8 +81,10 @@
     -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
     -- legacy-compatibility composition (serialize, hash, package); otherwise emit
     -- the standard form. The legacy branch is the behavior the change introduces.
+    -- WRONG(deep-composition): legacy branch packages the hash with the hash
+    -- instead of with the serialized form (wrong second argument to wrap).
     let result : Encoded :=
-      if legacyHashMode then legacyEncoding sessionData
+      if legacyHashMode then wrap (hashOf (serialize sessionData)) (hashOf (serialize sessionData))
       else standardEncoding sessionData
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real encoder always terminates (it is a straight-line
   dispatch over pure serialization/signing calls), so a diverging implementation
   must NOT satisfy this spec. Partial correctness would let a non-terminating
   branch discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Carriers, identified abstractly (mapping.md §2): a piece of session data, its
   serialized byte form, a content hash of that form, and the final textual
   encoding. Only the textual encoding is observed by callers; the intermediate
   carriers exist so the legacy encoding can be modeled as the exact composition
   of the unchanged building blocks it is built from (see `legacyEncoding`). -/
abbrev SessionData := Nat
abbrev Serialized  := Nat
abbrev Hash        := Nat
abbrev Encoded     := Nat

/- The UNCHANGED building blocks the encoder delegates to. None is the operation
   under spec (the dispatch + the legacy composition are spelled out below); each
   is a pre-existing community callee with published behavior. Provenance +
   executable soundness are in mapping.md §3 / axiom_check.py (G-AX).

   * `serialize` — turn a piece of session data into its serialized byte form.
   * `hashOf`    — a salted keyed content hash of a serialized form.
   * `wrap`      — combine a hash and a serialized form into one textual blob
                   (a reversible packaging of the two).
   * `standardEncoding` — the standard signed-and-compressed textual encoding,
                   together with the standard loader that inverts it.

   These are modeled as opaque functions: the spec pins the encoder's output to
   compositions of them, never to a free-floating oracle (directive 8). G-AX
   binds each to its real callee and checks the legacy composition is read back
   by the long-standing legacy reader, and the standard encoding by its loader. -/
opaque serialize        : SessionData → Serialized
opaque hashOf           : Serialized → Hash
opaque wrap             : Hash → Serialized → Encoded
opaque standardEncoding : SessionData → Encoded
-- axioms-end

-- pure-start
/- The legacy-compatibility textual encoding of a piece of session data, modeled
   as the exact composition of the unchanged building blocks: serialize it, hash
   the serialized form, then package the hash together with the serialized form
   into one reversible textual blob. This is the form the long-standing legacy
   reader can read back unchanged — the behavior the public report asks for when
   the legacy hashing-algorithm mode is in effect. -/
def legacyEncoding (d : SessionData) : Encoded :=
  wrap (hashOf (serialize d)) (serialize d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Serialize and encode a piece of session data into its textual form.

   Desired behavior: the encoder is consulted together with a flag selecting the
   legacy hashing-algorithm mode (the sha1 setting the public report names). When
   that legacy mode is in effect, the encoder must emit the legacy-compatibility
   form — serialized, hashed, and packaged so the long-standing legacy reader can
   read it back unchanged; the public report's exact failure is that, in this
   mode, written data could not be decoded back by another running instance. When
   the legacy mode is NOT in effect, the encoder emits the standard form.

   `sessionData` and `legacyHashMode` are read-only (neither is `mut`): the
   encoder produces a textual form and mutates no input (directive 5). -/
method encodeSession (sessionData : SessionData) (legacyHashMode : Bool)
    return (out : Encoded)
  ensures legacyHashMode = true  → out = legacyEncoding sessionData
  ensures legacyHashMode = false → out = standardEncoding sessionData
  do
    -- impl-start
    -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
    -- legacy-compatibility composition (serialize, hash, package); otherwise emit
    -- the standard form. The legacy branch is the behavior the change introduces.
    let result : Encoded :=
      if legacyHashMode then legacyEncoding sessionData
      else standardEncoding sessionData
    return result
    -- impl-end

prove_correct encodeSession by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec (encodeSession) pins output on BOTH branches by full equality under total-correctness/demonic-choice: `legacyHashMode=true -> out=legacyEncoding sessionData`, `false -> out=standardEncoding sessionData`, where legacyEncoding = wrap (hashOf (serialize d)) (serialize d) is a DEEP model (pure region), and serialize/hashOf/wrap/standardEncoding are opaque UNCHANGED building blocks.

Same_spec = True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec, velvet backend). Verifications run concurrently (<=4) via scripts/lean_verify.sh 300.

Attack results:
- atk_1 (swapped branches): EXIT 1 rejected. Residual goal legacyHashMode=true -> standardEncoding=legacyEncoding (false over distinct opaque fns).
- atk_2 (always-legacy, ignores mode): EXIT 1 rejected (fails standard-mode clause).
- atk_3 (always-standard = prepatch bug): EXIT 1 rejected; goal standardEncoding=legacyEncoding unprovable.
- atk_4 (partial-domain: standard branch emits legacy form): EXIT 1 rejected.
- atk_5 (negated-flag control-flow-effect): EXIT 1 rejected.
- atk_7 (ungrounded/wrong deep composition: wrap hash with hash instead of serialized): EXIT 1 rejected; goal wrap h h = legacyEncoding unprovable.
- atk_6 (CORRECT echo, syntactically distinct: match on flag + inline `wrap (hashOf (serialize sessionData)) (serialize sessionData)`; proof `loom_solve <;> simp_all [legacyEncoding]`): EXIT 0 VERIFIES.

Per protocol every VERIFYING wrong-impl's faithful refined patch must be run through run_resolve. atk_6 is the ONLY non-positive-control impl that verifies, and it is behaviorally identical to gold (same output on every (data,mode)), so its faithful refined patch IS the gold patch verbatim. run_resolve('django__django-13279', gold_patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved' (log: resolve_atk6.log). Its faithful patch resolves -> no verify-not-resolve gap. NO verifying impl produces a non-resolving faithful patch.

prepatch (Solution_prepatch.lean, always-standard) reproduced independently: EXIT 1, fails exactly the legacy-mode clause (G-DIFF).

Refinement.md audit: legs A1(R), A2(R), A3(I), A4(A-reference+I), A5(A-reference), A6(R). NO kind-3 step; the genuinely-changed op (flag dispatch + legacy encoding) is modeled concretely (A3 if) and deeply (A4 legacyEncoding composition), never behind a consumed Prop axiom about the function-under-change. A-reference correspondence holds: serialize=self.serializer().dumps, hashOf=SessionBase._hash (base.py:104, unchanged/present at base), wrap=base64.b64encode(hash.encode()+b':'+serialized).decode('ascii'), standardEncoding=signing.dumps(...,compress=True) (base.py:111, unchanged). G-AX (meta.json) passes: legacy deep model decodable by unchanged _legacy_decode on 5007 payloads, standard roundtrip sound on 10014. All callees exist at base_commit; G-AX never calls patch-introduced _legacy_encode.

Commands:
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SPEC).read(),open(ATK).read(),b.language))"
  verify:   bash scripts/lean_verify.sh <atk>.lean
  resolve:  run_resolve('django__django-13279', gold_patch, timeout=1800)

Verdict: SOUND. >=6 distinct wrong impls (partial-domain, boundary/branch-swap, control-flow-effect, ungrounded-oracle deep-composition, prepatch) all correctly rejected; the sole verifying same-spec impl (correct echo) has a resolving faithful patch. verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real encoder always terminates (it is a straight-line
   dispatch over pure serialization/signing calls), so a diverging implementation
   must NOT satisfy this spec. Partial correctness would let a non-terminating
   branch discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Carriers, identified abstractly (mapping.md §2): a piece of session data, its
   serialized byte form, a content hash of that form, and the final textual
   encoding. Only the textual encoding is observed by callers; the intermediate
   carriers exist so the legacy encoding can be modeled as the exact composition
   of the unchanged building blocks it is built from (see `legacyEncoding`). -/
abbrev SessionData := Nat
abbrev Serialized  := Nat
abbrev Hash        := Nat
abbrev Encoded     := Nat

/- The UNCHANGED building blocks the encoder delegates to. None is the operation
   under spec (the dispatch + the legacy composition are spelled out below); each
   is a pre-existing community callee with published behavior. Provenance +
   executable soundness are in mapping.md §3 / axiom_check.py (G-AX).

   * `serialize` — turn a piece of session data into its serialized byte form.
   * `hashOf`    — a salted keyed content hash of a serialized form.
   * `wrap`      — combine a hash and a serialized form into one textual blob
                   (a reversible packaging of the two).
   * `standardEncoding` — the standard signed-and-compressed textual encoding,
                   together with the standard loader that inverts it.

   These are modeled as opaque functions: the spec pins the encoder's output to
   compositions of them, never to a free-floating oracle (directive 8). G-AX
   binds each to its real callee and checks the legacy composition is read back
   by the long-standing legacy reader, and the standard encoding by its loader. -/
opaque serialize        : SessionData → Serialized
opaque hashOf           : Serialized → Hash
opaque wrap             : Hash → Serialized → Encoded
opaque standardEncoding : SessionData → Encoded
-- axioms-end

-- pure-start
/- The legacy-compatibility textual encoding of a piece of session data, modeled
   as the exact composition of the unchanged building blocks: serialize it, hash
   the serialized form, then package the hash together with the serialized form
   into one reversible textual blob. This is the form the long-standing legacy
   reader can read back unchanged — the behavior the public report asks for when
   the legacy hashing-algorithm mode is in effect. -/
def legacyEncoding (d : SessionData) : Encoded :=
  wrap (hashOf (serialize d)) (serialize d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Serialize and encode a piece of session data into its textual form.

   Desired behavior: the encoder is consulted together with a flag selecting the
   legacy hashing-algorithm mode (the sha1 setting the public report names). When
   that legacy mode is in effect, the encoder must emit the legacy-compatibility
   form — serialized, hashed, and packaged so the long-standing legacy reader can
   read it back unchanged; the public report's exact failure is that, in this
   mode, written data could not be decoded back by another running instance. When
   the legacy mode is NOT in effect, the encoder emits the standard form.

   `sessionData` and `legacyHashMode` are read-only (neither is `mut`): the
   encoder produces a textual form and mutates no input (directive 5). -/
method encodeSession (sessionData : SessionData) (legacyHashMode : Bool)
    return (out : Encoded)
  ensures legacyHashMode = true  → out = legacyEncoding sessionData
  ensures legacyHashMode = false → out = standardEncoding sessionData
  do
    -- impl-start
    -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
    -- legacy-compatibility composition (serialize, hash, package); otherwise emit
    -- the standard form. The legacy branch is the behavior the change introduces.
    let result : Encoded :=
      if legacyHashMode then legacyEncoding sessionData
      else standardEncoding sessionData
    return result
    -- impl-end

prove_correct encodeSession by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec (encodeSession) pins output on BOTH branches by full equality under total-correctness/demonic-choice: `legacyHashMode=true -> out=legacyEncoding sessionData`, `false -> out=standardEncoding sessionData`, where legacyEncoding = wrap (hashOf (serialize d)) (serialize d) is a DEEP model (pure region), and serialize/hashOf/wrap/standardEncoding are opaque UNCHANGED building blocks.

Same_spec = True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec, velvet backend). Verifications run concurrently (<=4) via scripts/lean_verify.sh 300.

Attack results:
- atk_1 (swapped branches): EXIT 1 rejected. Residual goal legacyHashMode=true -> standardEncoding=legacyEncoding (false over distinct opaque fns).
- atk_2 (always-legacy, ignores mode): EXIT 1 rejected (fails standard-mode clause).
- atk_3 (always-standard = prepatch bug): EXIT 1 rejected; goal standardEncoding=legacyEncoding unprovable.
- atk_4 (partial-domain: standard branch emits legacy form): EXIT 1 rejected.
- atk_5 (negated-flag control-flow-effect): EXIT 1 rejected.
- atk_7 (ungrounded/wrong deep composition: wrap hash with hash instead of serialized): EXIT 1 rejected; goal wrap h h = legacyEncoding unprovable.
- atk_6 (CORRECT echo, syntactically distinct: match on flag + inline `wrap (hashOf (serialize sessionData)) (serialize sessionData)`; proof `loom_solve <;> simp_all [legacyEncoding]`): EXIT 0 VERIFIES.

Per protocol every VERIFYING wrong-impl's faithful refined patch must be run through run_resolve. atk_6 is the ONLY non-positive-control impl that verifies, and it is behaviorally identical to gold (same output on every (data,mode)), so its faithful refined patch IS the gold patch verbatim. run_resolve('django__django-13279', gold_patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved' (log: resolve_atk6.log). Its faithful patch resolves -> no verify-not-resolve gap. NO verifying impl produces a non-resolving faithful patch.

prepatch (Solution_prepatch.lean, always-standard) reproduced independently: EXIT 1, fails exactly the legacy-mode clause (G-DIFF).

Refinement.md audit: legs A1(R), A2(R), A3(I), A4(A-reference+I), A5(A-reference), A6(R). NO kind-3 step; the genuinely-changed op (flag dispatch + legacy encoding) is modeled concretely (A3 if) and deeply (A4 legacyEncoding composition), never behind a consumed Prop axiom about the function-under-change. A-reference correspondence holds: serialize=self.serializer().dumps, hashOf=SessionBase._hash (base.py:104, unchanged/present at base), wrap=base64.b64encode(hash.encode()+b':'+serialized).decode('ascii'), standardEncoding=signing.dumps(...,compress=True) (base.py:111, unchanged). G-AX (meta.json) passes: legacy deep model decodable by unchanged _legacy_decode on 5007 payloads, standard roundtrip sound on 10014. All callees exist at base_commit; G-AX never calls patch-introduced _legacy_encode.

Commands:
  same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SPEC).read(),open(ATK).read(),b.language))"
  verify:   bash scripts/lean_verify.sh <atk>.lean
  resolve:  run_resolve('django__django-13279', gold_patch, timeout=1800)

Verdict: SOUND. >=6 distinct wrong impls (partial-domain, boundary/branch-swap, control-flow-effect, ungrounded-oracle deep-composition, prepatch) all correctly rejected; the sole verifying same-spec impl (correct echo) has a resolving faithful patch. verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attempt failed — no diverging input exists. Verified: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) = True — spec regions (axioms/pure/pre/post/method signature+ensures) are byte-identical; the discriminating content lives only in the impl region, which is excluded from the spec view. (2) Solution.lean verifies via scripts/lean_verify.sh (exit 0). (3) Solution_prepatch.lean fails EXACTLY on the legacy-mode clause `legacyHashMode = true → standardEncoding = wrap(hashOf(serialize),serialize)` (G-DIFF discriminates). (4) The real repo at base_commit 6e9c5ee88f confirms the modeling: `encode` = `if DEFAULT_HASHING_ALGORITHM=='sha1': return _legacy_encode(d)` else `signing.dumps(...,compress=True)`. The gold `_legacy_encode` = `b64encode(_hash(serializer().dumps(d)).encode()+b':'+serialized).decode('ascii')`, which is EXACTLY the deep model `legacyEncoding d = wrap(hashOf(serialize d), serialize d)` under the mapping.md bindings (serialize=serializer().dumps, hashOf=_hash, wrap=base64 packaging). The standard branch is left opaque (standardEncoding) and not over-committed. 

Drift checks: (a) Legacy branch matched byte-for-byte by G-CONF over 10^5 inputs across both modes, 0 disagreements. (b) The Bool abstraction of DEFAULT_HASHING_ALGORITHM (True↔'sha1', False↔otherwise) faithfully captures the single dispatch bit the patch introduced; although signing.dumps's HMAC algorithm depends on the setting value, that is pre-existing UNCHANGED behavior and standardEncoding is opaque (not pinned to any algorithm-specific value), so no formal disagreement can be exhibited on the false branch. (c) No non-termination / partiality gap: total-correctness semantics is set, and the impl is a straight-line dispatch. The spec is neither too strong nor drifted from real behavior — for sha1 the real output is precisely the deep composition, for non-sha1 it is the opaque standard path. FAITHFUL with no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, 0 hard failures). same_spec(Solution, Solution_prepatch)=True; the impl/proof regions are properly elided from the consumer spec view (verified via markers.spec_view). Semantic review confirms no leak beyond the public problem_statement:

- problem_statement already discloses verbatim: 'DEFAULT_HASHING_ALGORITHM', 'sha1', session data 'cannot be decoded' across 'multiple instances' during the 3.1 transition, AND the exact fix strategy: 'We could use the legacy encode() when DEFAULT_HASHING_ALGORITHM == 'sha1''. So the dispatch-on-sha1-to-legacy-encoding idea is PUBLIC.

- Spec view models the changed function abstractly: SessionData/Serialized/Hash/Encoded are opaque Nat carriers; serialize/hashOf/wrap/standardEncoding are opaque functions described only generically ('salted keyed content hash', 'reversible textual blob', 'standard signed-and-compressed encoding'). It does NOT name the gold-edit specifics: no '_legacy_encode', no 'base64', no 'signing.dumps', no b':' separator, no salt=key_salt/compress=True, and no patched file path (django/contrib/sessions/backends/base.py absent from view).

- The postconditions (legacyHashMode -> legacyEncoding sessionData; else standardEncoding sessionData) and legacyEncoding = wrap (hashOf (serialize d)) (serialize d) express the generic notion of an encoder dispatch, which is exactly what the public 'legacy encode() when ... == sha1' phrasing already communicates — not the concrete gold code.

- Narration screen clean; patch-changed distinctive symbols {legacy_encode, hash, decode} are not echoed as spec-view identifiers, and no changed-line >=8 chars is reproduced. Comments carry no bug/fix narration.

Conclusion: the spec view leaks nothing about the gold edit beyond what problem_statement already makes public. meta.json records G-LEAK pass (not relaxed); consistent.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
